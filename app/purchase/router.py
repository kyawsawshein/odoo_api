"""Main API router for Odoo FastAPI integration"""

from typing import List

import structlog
from app.api.models import SyncResponse
from app.purchase.models.model import (
    PurchaseOrder,
    PurchaseOrderCreate,
)
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.purchase.route_name import Route

from app.database import get_db

# from app.kafka.producer import KafkaProducer
from app.purchase.purchase_service import PurchaseService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/purchase", tags=["Purchase"])


# Purchase Order Endpoints
@router.post(Route.purchase_order, response_model=SyncResponse)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new purchase order and sync with Odoo"""
    service = PurchaseService(db, current_user)
    try:
        result = await service.create_purchase_order(order.dict())
        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-purchase",
        #     {
        #         "action": "create",
        #         "user_id": current_user.id,
        #         "order_data": order.dict(),
        #         "local_id": result.local_id
        #     }
        # )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create purchase order: {str(e)}",
        )


@router.get(Route.purchase_order, response_model=List[PurchaseOrder])
async def get_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get purchase orders"""
    service = PurchaseService(db, current_user)
    return await service.get_purchase_orders(skip=skip, limit=limit)
