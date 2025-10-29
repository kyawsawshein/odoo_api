"""Main API router for Odoo FastAPI integration"""

# from typing import List, Optional

import structlog
from app.bulk_sync.models.model import (
    BulkSyncRequest,
    BulkSyncResponse,
)
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema

from app.kafka.producer import KafkaProducer

# from app.cache.redis_client import redis_client
from app.database import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


# Bulk Operations
@router.post("/bulk-sync", response_model=BulkSyncResponse, tags=["bulk"])
async def bulk_sync(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk sync multiple entities with Odoo"""
    try:
        # Send to Kafka for async bulk processing
        background_tasks.add_task(
            KafkaProducer.send_message,
            "odoo-bulk-sync",
            {"user_id": current_user.id, "data": request.dict()},
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
