"""Inventory service for managing inventory and Odoo synchronization"""

from typing import List, Optional, Any

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# from app.auth.schemas import User as UserSchema
from app.api.models.models import SyncResponse
from app.inventory.services.category import CategoryService
from app.inventory.services.uom import UomService
from app.inventory.schemas.schemas import Inventory as InventorySchema


class Inventory(UomService, CategoryService):
    """Service for inventory operations"""

    async def get_inventory(self, product_id: Optional[int] = None) -> List[Any]:
        """Get inventory data"""
        cache_key = f"inventory:{self.current_user.id}:{product_id}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        stmt = select(InventorySchema).where(
            InventorySchema.user_id == self.current_user.id
        )

        if product_id:
            stmt = stmt.where(InventorySchema.product_id == product_id)

        result = await self.db.execute(stmt)
        inventory = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, inventory, expire=300)

        return inventory
