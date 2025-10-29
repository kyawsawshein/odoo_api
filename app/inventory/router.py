"""Main API router for Odoo FastAPI integration"""

from typing import List, Optional

import structlog
from app.api.models import SyncResponse
from app.inventory.models.model import Inventory
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema

from app.inventory.route_name import Route

from app.database import get_db
# from app.kafka.producer import KafkaProducer
from app.inventory.inventory_service import InventoryService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# Inventory Endpoints
@router.get(Route.inventory, response_model=List[Inventory])
async def get_inventory(
    product_id: Optional[int] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get inventory data"""
    service = InventoryService(db, current_user)
    return await service.get_inventory(product_id=product_id)


@router.post(Route.inventory_sync, response_model=SyncResponse)
async def sync_inventory(
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync inventory data with Odoo"""
    service = InventoryService(db, current_user)

    try:
        result = await service.sync_inventory()
        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-inventory",
        #     {
        #         "action": "sync",
        #         "user_id": current_user.id
        #     }
        # )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync inventory: {str(e)}",
        )
