"""Frontend API router for project and task management with Odoo synchronization"""

import asyncio
import os
import uuid
from typing import List, Optional

import aiofiles
import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    Query,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.auth.session_auth import get_session_odoo_connection

from app.api.models.models import SyncResponse
from app.auth.api.v1 import validate_token
from app.dependency import db
from app.validate.api.route_name import Route
from app.validate.controllers.controller import ValidateController
from app.validate.helper import task_store
from app.validate.helper.helper import (
    OUTPUT_DIR,
    UPLOAD_DIR,
    _cleanup_dir,
    _safe_remove,
)
from app.validate.helper.parsers.factory import get_parser
from app.validate.helper.spreadsheet_parser import parse_spreadsheet
from app.validate.helper.tasks import process_po, run_verification
from app.validate.models.model import (
    CleanupRequest,
    SyncProductsRequest,
    SyncProductsResponse,
    VerifyRequest,
)
from app.validate.schemas.response import ResponseSchema

logger = structlog.get_logger()


router = APIRouter(
    prefix="/validate",
    tags=["Validate"],
    dependencies=[Depends(validate_token)],
)


async def _process_po_task(
    task_id: str,
    pdf_path: str,
    customer_name: str,
    po_number: str | None,
):
    """Runs process_po in the background and updates the task store.

    Called via asyncio.create_task() from the /upload-po endpoint so it
    runs concurrently with future requests without blocking the response.
    """
    task_store.set_processing(task_id)
    try:
        result = await process_po(pdf_path, customer_name, po_number)
        task_store.set_done(task_id, result)
        print(
            f"[Task] {task_id} done: {result['existing_count']} existing, {result['missing_count']} missing"
        )
    except Exception as exc:
        task_store.set_error(task_id, str(exc))
        print(f"[Task] {task_id} failed: {exc}")
    finally:
        _safe_remove(pdf_path)  # always clean up the uploaded PDF




# ── Step 1: Extract PO data (no DB, no verification) ──────────────────


@router.post(Route.extract_po)
async def extract_po(
    customer_name: str = Form("zervi"),
    file: UploadFile = File(...),
):
    """Upload a PO PDF, extract all 8 columns, return raw data for editing."""
    filename = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, filename)

    try:
        async with aiofiles.open(pdf_path, "wb") as out_file:
            content = await file.read()
            print(
                f"[Extract] Received {file.filename} ({len(content)} bytes) → {pdf_path}"
            )
            await out_file.write(content)

        parser = get_parser(customer_name)
        products = parser.parse(pdf_path)

        print(f"[Extract] Parsed {len(products)} products for {customer_name}")
        return {
            "products": products,
            "product_count": len(products),
        }
    finally:
        _safe_remove(pdf_path)


# ── Step 1b: Extract data from CSV / Excel ───────────────────────────


@router.post(Route.extract_file)
async def extract_file(
    file: UploadFile = File(...),
):
    """Upload a CSV or Excel file, extract all 8 columns, return raw data."""
    content = await file.read()
    print(f"[Extract-File] Received {file.filename} ({len(content)} bytes)")

    products = parse_spreadsheet(content, file.filename or "")

    print(f"[Extract-File] Parsed {len(products)} products")
    return {
        "products": products,
        "product_count": len(products),
    }


# ── Step 2: Verify (potentially edited) products ───────────────────────


@router.post(Route.verify_po)
async def verify_po(body: VerifyRequest):
    """Receive a (potentially user-edited) product list and run 6-step verification."""
    products = [p.model_dump() for p in body.products]

    print(
        f"[Verify] Received {len(products)} products "
        f"for customer '{body.customer_name}'"
    )

    result = await run_verification(
        products,
        body.customer_name,
        body.po_number,
    )
    print(
        f"[Verify] Done: {result['existing_count']} existing, "
        f"{result['missing_count']} missing"
    )
    return result


# ── Combined endpoint (backward-compatible) ────────────────────────────


@router.post(Route.upload_po)
async def upload_po(
    customer_name: str = Form("zervi"),
    po_number: str = Form(None),
    file: UploadFile = File(...),
):
    """Upload a PO PDF. Returns task_id immediately; processing runs in background.

    Poll GET /task/{task_id} to check progress and retrieve results.
    """
    task_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{task_id}.pdf")

    async with aiofiles.open(pdf_path, "wb") as out_file:
        content = await file.read()
        print(f"[Upload] {file.filename} ({len(content)} bytes) → {pdf_path}")
        await out_file.write(content)

    task_store.create_task(task_id)
    asyncio.create_task(_process_po_task(task_id, pdf_path, customer_name, po_number))
    print(f"[Upload] Started background task {task_id} for customer '{customer_name}'")
    return {"task_id": task_id}


# ── Task polling ────────────────────────────────────────────────────────


@router.get(Route.task)
async def get_task_status(task_id: str):
    """Poll the status of a background PO processing job.

    Response shapes:
      {"status": "pending"}                          — not yet started
      {"status": "processing"}                       — running
      {"status": "done", "result": {...}}            — finished; result contains
                                                       excel_file, existing, missing,
                                                       existing_count, missing_count,
                                                       markdown_report
      {"status": "error", "error": "<message>"}     — failed
    """
    from fastapi import HTTPException

    task = task_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] == "done":
        return {"status": "done", "result": task["result"]}
    if task["status"] == "error":
        return {"status": "error", "error": task["error"]}
    return {"status": task["status"]}  # "pending" or "processing"


# ── Static files & cleanup ──────────────────────────────────────────────


@router.get(Route.download)
async def download_file(filename: str, background_tasks: BackgroundTasks):
    """Serve an Excel file, then schedule it for deletion."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(file_path):
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found")

    # Schedule deletion after the response has been sent
    background_tasks.add_task(_safe_remove, file_path)
    return FileResponse(path=file_path, filename=filename)


@router.post(Route.cleanup)
async def cleanup(body: CleanupRequest = CleanupRequest()):
    """Delete temporary files.

    - `filenames`: delete specific files from outputs/
    - `all_outputs`: delete everything in outputs/
    - `all_uploads`: delete everything in uploads/
    """
    removed = []

    if body.filenames:
        for fname in body.filenames:
            # Sanitize: only allow alphanumeric, dash, underscore, dot
            safe = "".join(c for c in fname if c.isalnum() or c in "-_.")
            if safe == fname:
                path = os.path.join(OUTPUT_DIR, safe)
                if os.path.isfile(path):
                    _safe_remove(path)
                    removed.append(safe)

    if body.all_outputs:
        _cleanup_dir(OUTPUT_DIR)
        removed.append("all outputs")

    if body.all_uploads:
        _cleanup_dir(UPLOAD_DIR)
        removed.append("all uploads")

    return {"removed": removed}


@router.get(Route.health)
async def health_check():
    """Verify database connectivity."""
    try:
        from app.db import get_pool

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Differential sync ─────────────────────────────────────────────────


@router.post(
    Route.sync_products,
    response_model=SyncProductsResponse,
)
async def sync_products(
    limit: int = 100,
    write_date: Optional[str] = None,
    body: SyncProductsRequest = SyncProductsRequest(),
    customer: str = Query("zervi", description="Customer name for auto-fetched records"),
    odoo_connection=Depends(get_session_odoo_connection),
):
    """Batch-insert product_info and product_category records.

    Two modes:
      - **Explicit**: provide ``product_info`` / ``product_category`` in the request body.
      - **Auto-fetch**: leave the body empty (or omit fields) — data is pulled from
        Odoo's ``/product/products`` and ``/product/pricelists`` endpoints.

    Only records whose ``last_record`` timestamp is strictly greater than
    the current ``MAX(last_record)`` in each table are persisted.
    """
    return await ValidateController(odoo_connection).sync_products(
        body, customer, limit, write_date
    )
