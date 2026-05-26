"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator, model_validator

# ── Pydantic models ────────────────────────────────────────────────────


class ProductItem(BaseModel):
    sku: str
    product_name: str = ""
    barcode: Optional[str] = ""
    supplier_code: Optional[str] = ""
    job_no: Optional[str] = ""
    qty: Optional[int] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None


class VerifyRequest(BaseModel):
    customer_name: str = "zervi"
    po_number: Optional[str] = None
    products: list[ProductItem]


class CleanupRequest(BaseModel):
    filenames: Optional[list[str]] = None
    """Specific filenames to delete from OUTPUT_DIR."""
    all_outputs: bool = False
    """Delete all files in OUTPUT_DIR."""
    all_uploads: bool = False
    """Delete all files in UPLOAD_DIR."""


# ── Sync models ────────────────────────────────────────────────────────


class ProductInfoSyncItem(BaseModel):
    """A single record to upsert into product_info."""

    sku: str
    barcode: Optional[str] = ""
    product: str = ""
    category: str = ""
    customer: str = ""
    price: Optional[float] = None
    last_record: Optional[datetime] = None


class ProductCategorySyncItem(BaseModel):
    """A single record to insert into product_category."""

    product: str = ""
    category: str = ""
    customer: str = ""
    price: Optional[float] = None
    last_record: Optional[datetime] = None


class SyncProductsRequest(BaseModel):
    """Batch sync request — only records newer than current MAX(last_record) are inserted."""

    product_info: list[ProductInfoSyncItem] = []
    product_category: list[ProductCategorySyncItem] = []


class SyncProductsResponse(BaseModel):
    """Result of a batch sync operation."""

    product_info_inserted: int = 0
    product_info_updated: int = 0
    product_category_inserted: int = 0
    product_info_max_before: Optional[str] = None
    product_category_max_before: Optional[str] = None
    detail: str = ""
