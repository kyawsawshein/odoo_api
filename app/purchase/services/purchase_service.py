"""Purchase service for managing purchase orders and Odoo synchronization"""

from typing import Any, Dict, List

# from app.auth.schemas import User as UserSchema
from app.api.models.models import SyncResponse
from app.services.base_service import BaseService

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class PurchaseService(BaseService):
    """Service for purchase operations"""

    async def create_purchase_order(self, order_data: Dict[str, Any]) -> SyncResponse:
        """Create purchase order in local database and sync with Odoo"""
        try:
            # First create in local database
            from app.api.schemas import PurchaseOrder as PurchaseOrderSchema

            db_order = PurchaseOrderSchema(**order_data, user_id=self.current_user.id)
            self.db.add(db_order)
            await self.db.commit()
            await self.db.refresh(db_order)

            # Then sync with Odoo
            odoo_client = await self._get_odoo_client()
            odoo_id = await odoo_client.create_purchase_order(order_data)

            # Update local record with Odoo ID
            db_order.odoo_id = odoo_id
            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"purchase_orders:{self.current_user.id}")

            self.logger.info(
                "Purchase order created successfully",
                order_id=db_order.id,
                odoo_id=odoo_id,
            )

            return self._create_sync_response(
                success=True,
                message="Purchase order created and synced with Odoo",
                odoo_id=odoo_id,
                local_id=db_order.id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "purchase order creation")

    async def get_purchase_orders(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get purchase orders"""
        cache_key = f"purchase_orders:{self.current_user.id}:{skip}:{limit}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        from app.api.schemas import PurchaseOrder as PurchaseOrderSchema

        stmt = (
            select(PurchaseOrderSchema)
            .where(PurchaseOrderSchema.user_id == self.current_user.id)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, orders, expire=300)

        return orders
