"""Purchase service for managing purchase orders and Odoo synchronization"""

from typing import List, Dict, Any, Optional

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
from sqlalchemy import select, func

from app.api.models.models import SyncResponse
from app.services.base_service import BaseService
from app.account.schemas import Currency as CurrencySchema


class AccountingService(BaseService):
    """Service for purchase operations"""

    async def create_purchase_order(self, order_data: Dict[str, Any]) -> SyncResponse:
        """Create purchase order in local database and sync with Odoo"""
        pass

    async def get_purchase_orders(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get purchase orders"""
        pass

    async def get_currency(self, currency: str) -> Optional[Any]:
        """Get specific contact by ID"""
        cache_key = f"currency:{str}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        stmt = select(CurrencySchema).where(CurrencySchema.name == currency)
        result = await self.db.execute(stmt)
        contact = result.scalar_one_or_none()
        if contact:
            await self._cache_set(cache_key, contact, expire=300)

        return contact


    async def sync_currency_from_odoo(self, full: bool = False) -> SyncResponse:
        """Sync contacts from Odoo to local database"""
        try:
            domain = []
            if not full:
                stmt = select(func.max(CurrencySchema.write_date))
                result = await self.db.execute(stmt)
                last_updated_date = result.scalar_one_or_none()
                if last_updated_date:
                    domain = [("write_date", ">", last_updated_date)]

            odoo_client = await self._get_odoo_client()
            odoo_currencies = await odoo_client.search_currency(domain=domain)

            synced_count = 0
            for odoo_currency in odoo_currencies:
                stmt = select(CurrencySchema).where(
                    CurrencySchema.odoo_id == odoo_currency.id
                )
                result = await self.db.execute(stmt)
                existing_contact = result.scalar_one_or_none()
                if existing_contact:
                    # Update existing contact
                    for field, value in odoo_currency.model_dump(exclude=None).items():
                        self.logger.info(f"Update data, Key : {field}, Value : {value}")
                        if hasattr(existing_contact, field) and value:
                            setattr(existing_contact, field, value)
                else:
                    db_currency = CurrencySchema(**odoo_currency.model_dump(exclude=None))
                    db_currency.id = None
                    db_currency.odoo_id = odoo_currency.id
                    self.db.add(db_currency)
                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"currency:{self.current_user.id}")
            self.logger.info("Currency synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} currency from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "currency sync from Odoo")
