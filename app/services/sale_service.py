"""Sale service for managing sale orders and Odoo synchronization"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.services.base_service import BaseService


class SaleService(BaseService):
    """Service for sale operations"""
    
    async def create_sale_order(self, order_data: Dict[str, Any]) -> SyncResponse:
        """Create sale order in local database and sync with Odoo"""
        try:
            # First create in local database
            from app.api.schemas import SaleOrder as SaleOrderSchema
            db_order = SaleOrderSchema(**order_data, user_id=self.current_user.id)
            self.db.add(db_order)
            await self.db.commit()
            await self.db.refresh(db_order)
            
            # Then sync with Odoo
            odoo_client = await self._get_odoo_client()
            odoo_id = await odoo_client.create_sale_order(order_data)
            
            # Update local record with Odoo ID
            db_order.odoo_id = odoo_id
            await self.db.commit()
            
            # Clear cache
            await self._cache_delete(f"sale_orders:{self.current_user.id}")
            
            self.logger.info(
                "Sale order created successfully", 
                order_id=db_order.id, 
                odoo_id=odoo_id
            )
            
            return self._create_sync_response(
                success=True,
                message="Sale order created and synced with Odoo",
                odoo_id=odoo_id,
                local_id=db_order.id
            )
            
        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "sale order creation")
    
    async def get_sale_orders(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get sale orders"""
        cache_key = f"sale_orders:{self.current_user.id}:{skip}:{limit}"
        
        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached
        
        # Query from database
        from app.api.schemas import SaleOrder as SaleOrderSchema
        stmt = select(SaleOrderSchema).where(
            SaleOrderSchema.user_id == self.current_user.id
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        orders = result.scalars().all()
        
        # Cache the result
        await self._cache_set(cache_key, orders, expire=300)
        
        return orders