"""Purchase service for managing purchase orders and Odoo synchronization"""

from typing import List, Dict, Any

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from app.auth.schemas import User as UserSchema
from app.api.models.models import SyncResponse
from app.services.base_service import BaseService


class DeliveryService(BaseService):
    """Service for purchase operations"""

    async def create_purchase_order(self, order_data: Dict[str, Any]) -> SyncResponse:
        """Create purchase order in local database and sync with Odoo"""
        pass

    async def get_purchase_orders(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get purchase orders"""
        pass
