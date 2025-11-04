"""Main API router for Odoo FastAPI integration"""

from typing import List

import structlog
from app.api.models.models import SyncResponse
from app.sale.models.model import (
    SaleOrder,
    SaleOrderCreate,
)
from app.auth.router import get_current_user
from app.auth.models.models import User
from app.sale.api.route_name import Route

# from app.kafka.producer import KafkaProducer
from app.core.database import get_db
from app.sale.services.sale_service import SaleService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/sale", tags=["Sale"])


# Sale Order Endpoints
@router.post(Route.sale_order, response_model=SyncResponse)
async def create_sale_order(
    order: SaleOrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sale order and sync with Odoo"""
    service = SaleService(db, current_user)

    try:
        result = await service.create_sale_order(order.dict())
        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-sales",
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
            detail=f"Failed to create sale order: {str(e)}",
        )


@router.get(Route.sale_order, response_model=List[SaleOrder])
async def get_sale_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sale orders"""
    service = SaleService(db, current_user)
    return await service.get_sale_orders(skip=skip, limit=limit)
