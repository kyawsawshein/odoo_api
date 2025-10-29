"""Inventory service for managing inventory and Odoo synchronization"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.services.base_service import BaseService


class InventoryService(BaseService):
    """Service for inventory operations"""

    async def get_inventory(self, product_id: Optional[int] = None) -> List[Any]:
        """Get inventory data"""
        cache_key = f"inventory:{self.current_user.id}:{product_id}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        from app.api.schemas import Inventory as InventorySchema

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

    async def sync_inventory(self) -> SyncResponse:
        """Sync inventory data from Odoo"""
        try:
            odoo_client = await self._get_odoo_client()

            # Get stock quantities from Odoo
            odoo_stock = await odoo_client.get_stock_quantities()

            from app.api.schemas import Inventory as InventorySchema

            synced_count = 0
            for stock_item in odoo_stock:
                product_id = stock_item.get("product_id")
                if not product_id:
                    continue

                # Check if inventory record exists
                stmt = select(InventorySchema).where(
                    InventorySchema.product_id
                    == product_id[0],  # Odoo returns [id, name]
                    InventorySchema.user_id == self.current_user.id,
                )
                result = await self.db.execute(stmt)
                existing_inventory = result.scalar_one_or_none()

                if existing_inventory:
                    # Update existing inventory
                    existing_inventory.quantity = stock_item.get("quantity", 0)
                    existing_inventory.location_id = (
                        stock_item.get("location_id")[0]
                        if stock_item.get("location_id")
                        else None
                    )
                else:
                    # Create new inventory record
                    inventory_data = {
                        "product_id": product_id[0],
                        "quantity": stock_item.get("quantity", 0),
                        "location_id": (
                            stock_item.get("location_id")[0]
                            if stock_item.get("location_id")
                            else None
                        ),
                        "user_id": self.current_user.id,
                    }
                    db_inventory = InventorySchema(**inventory_data)
                    self.db.add(db_inventory)

                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"inventory:{self.current_user.id}")

            self.logger.info("Inventory synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} inventory items from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "inventory sync")

    async def update_inventory_level(
        self, product_id: int, quantity: float
    ) -> SyncResponse:
        """Update inventory level and sync with Odoo"""
        try:
            # Get inventory record
            from app.api.schemas import Inventory as InventorySchema

            stmt = select(InventorySchema).where(
                InventorySchema.product_id == product_id,
                InventorySchema.user_id == self.current_user.id,
            )
            result = await self.db.execute(stmt)
            inventory = result.scalar_one_or_none()

            if not inventory:
                return self._create_sync_response(
                    success=False,
                    message="Inventory record not found",
                    errors=["Inventory record not found"],
                )

            # Update local record
            inventory.quantity = quantity
            await self.db.commit()

            # Sync with Odoo if Odoo ID exists
            if inventory.odoo_id:
                odoo_client = await self._get_odoo_client()
                # Create inventory adjustment in Odoo
                adjustment_data = {
                    "name": f"API Inventory Adjustment - Product {product_id}",
                    "location_ids": (
                        [(6, 0, [inventory.location_id])]
                        if inventory.location_id
                        else []
                    ),
                    "state": "confirm",
                }
                adjustment_id = await odoo_client.update_inventory(adjustment_data)

                # Create adjustment line
                line_data = {
                    "inventory_id": adjustment_id,
                    "product_id": product_id,
                    "product_qty": quantity,
                    "location_id": inventory.location_id,
                }
                await odoo_client.create_inventory_line(line_data)

            # Clear cache
            await self._cache_delete(f"inventory:{self.current_user.id}")
            await self._cache_delete(f"inventory:{self.current_user.id}:{product_id}")

            self.logger.info(
                "Inventory level updated", product_id=product_id, quantity=quantity
            )

            return self._create_sync_response(
                success=True,
                message="Inventory level updated and synced with Odoo",
                local_id=inventory.id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "inventory update")
