"""Main API router for Odoo FastAPI integration"""

# from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.auth.api.v1 import require_odoo_session, validate_token
from app.auth.models.models import User
from app.bulk_sync.api.route_name import Route
from app.bulk_sync.models.model import BulkSyncRequest, BulkSyncResponse
from app.dependency import db
from app.kafka.producer import kafka_producer

logger = structlog.get_logger()

router = APIRouter()
router = APIRouter(
    prefix="/bulk",
    tags=["Bulk"],
    dependencies=[Depends(validate_token)],
)


# Bulk Operations
@router.post(Route.bluk_sync, response_model=BulkSyncResponse)
async def bulk_sync(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_odoo_session),
):
    """Bulk sync multiple entities with Odoo"""
    try:
        # Send to Kafka for async bulk processing
        if kafka_producer.producer is None:
            # raise Exception("Kafka producer is not initialized")
            kafka_producer._connect()

        background_tasks.add_task(
            kafka_producer.send_message,
            "odoo-bulk-sync",
            {"user_id": current_user.id, "data": request.model_dump_json()},
        )

        return BulkSyncResponse(
            success=True,
            message="Bulk sync request queued for processing",
            results={},
            total_processed=0,
            total_success=0,
            total_failed=0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue bulk sync: {str(e)}",
        ) from e
