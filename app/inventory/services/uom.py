"""Inventory service for managing inventory and Odoo synchronization"""

from typing import List, Optional, Any

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.services.base_service import BaseService
from app.inventory.schemas import UomSchema


class UomService(BaseService):
    """Service for inventory operations"""

    async def get_uom(self, uom_name: Optional[str] = None) -> List[Any]:
        """Get inventory data"""
        cache_key = f"uom:{self.current_user.id}:{uom_name}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        stmt = select(UomSchema)
        if uom_name:
            stmt = stmt.where(UomSchema.name == uom_name)

        result = await self.db.execute(stmt)
        uom = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, uom, expire=300)

        return uom

    async def sync_uom_from_odoo(self, full: bool = False) -> SyncResponse:
        """Sync uom from Odoo to local database"""
        try:
            domain = []
            if not full:
                stmt = select(func.max(UomSchema.write_date))
                result = await self.db.execute(stmt)
                last_updated_date = result.scalar_one_or_none()
                if last_updated_date:
                    domain = [("write_date", ">", last_updated_date)]

            odoo_client = await self._get_odoo_client()
            odoo_uoms = await odoo_client.search_uom(domain=domain)
            synced_count = 0
            for odoo_uom in odoo_uoms:
                # Check if product already exists
                stmt = select(UomSchema).where(
                    UomSchema.odoo_id == odoo_uom.id
                )
                result = await self.db.execute(stmt)
                existing_uom = result.scalar_one_or_none()

                if existing_uom:
                    # Update existing product
                    for field, value in odoo_uom.model_dump(exclude=None).items():
                        if hasattr(existing_uom, field):
                            setattr(existing_uom, field, value)
                else:
                    db_uom = UomSchema(**odoo_uom.model_dump(exclude=None))
                    db_uom.id = None
                    db_uom.odoo_id = odoo_uom.id
                    self.db.add(db_uom)
                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"uom:{self.current_user.id}")

            self.logger.info("uom synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} uom from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "uom sync from Odoo")
