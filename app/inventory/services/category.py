"""Inventory service for managing inventory and Odoo synchronization"""

from typing import List, Optional, Any

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.services.base_service import BaseService
from app.inventory.schemas import CategorySchema


class CategoryService(BaseService):
    """Service for inventory operations"""

    async def get_category(self, category_name: Optional[str] = None) -> List[Any]:
        """Get Categories data"""
        cache_key = f"Categories:{self.current_user.id}:{category_name}"
        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        stmt = select(CategorySchema).where()
        if category_name:
            stmt = stmt.where(CategorySchema.name == category_name)

        result = await self.db.execute(stmt)
        category = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, category, expire=300)

        return category
    
    async def sync_category_from_odoo(self, full: bool = False) -> SyncResponse:
        """Sync categories from Odoo to local database"""
        try:
            domain = []
            if not full:
                stmt = select(func.max(CategorySchema.write_date))
                result = await self.db.execute(stmt)
                last_updated_date = result.scalar_one_or_none()
                if last_updated_date:
                    domain = [("write_date", ">", last_updated_date)]

            odoo_client = await self._get_odoo_client()
            odoo_uoms = await odoo_client.search_category(domain=domain)
            synced_count = 0
            for odoo_uom in odoo_uoms:
                # Check if product already exists
                stmt = select(CategorySchema).where(
                    CategorySchema.odoo_id == odoo_uom.id
                )
                result = await self.db.execute(stmt)
                existing_uom = result.scalar_one_or_none()

                if existing_uom:
                    # Update existing product
                    for field, value in odoo_uom.model_dump(exclude=None).items():
                        if hasattr(existing_uom, field):
                            setattr(existing_uom, field, value)
                else:
                    db_uom = CategorySchema(**odoo_uom.model_dump(exclude=None))
                    db_uom.id = None
                    db_uom.odoo_id = odoo_uom.id
                    self.db.add(db_uom)
                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"Categories:{self.current_user.id}")

            self.logger.info("Categories synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} Categories from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "Categories sync from Odoo")
