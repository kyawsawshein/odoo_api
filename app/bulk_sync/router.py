"""Main API router for Odoo FastAPI integration"""

# from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.v1 import get_current_user
from app.auth.models.models import User

# from app.cache.redis_client import redis_client
from app.auth.session_auth import get_odoo_session_user, get_session_odoo_connection
from app.bulk_sync.models.model import BulkSyncRequest, BulkSyncResponse
from app.dependency import db
from app.kafka.producer import kafka_producer

logger = structlog.get_logger()

router = APIRouter()


# Bulk Operations
@router.post("/bulk-sync", response_model=BulkSyncResponse, tags=["bulk"])
async def bulk_sync(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_odoo_session_user),
    db_connection=Depends(db.connection),
):
    """Bulk sync multiple entities with Odoo"""
    try:
        print("Kafka producer: ", kafka_producer)
        # Send to Kafka for async bulk processing
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
        )
