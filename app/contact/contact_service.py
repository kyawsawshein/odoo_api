"""Contact service for managing contacts and Odoo synchronization"""

import structlog
from typing import List, Optional, Dict, Any

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# from app.auth.schemas import User as UserSchema
from app.contact.schemas import Contact as ContactSchema
from app.api.models import SyncResponse
from app.services.base_service import BaseService

logger = structlog.get_logger()


class ContactService(BaseService):
    """Service for contact operations"""

    async def create_contact(self, contact_data: Dict[str, Any]) -> SyncResponse:
        """Create contact in local database and sync with Odoo"""
        try:
            # First create in local database
            db_contact = ContactSchema(**contact_data, user_id=self.current_user.id)
            self.db.add(db_contact)
            await self.db.commit()
            await self.db.refresh(db_contact)

            # Then sync with Odoo
            odoo_client = await self._get_odoo_client()
            odoo_id = await odoo_client.create_contact(contact_data)

            # Update local record with Odoo ID
            db_contact.odoo_id = odoo_id
            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"contacts:{self.current_user.id}")

            self.logger.info(
                "Contact created successfully",
                contact_id=db_contact.id,
                odoo_id=odoo_id,
            )

            return self._create_sync_response(
                success=True,
                message="Contact created and synced with Odoo",
                odoo_id=odoo_id,
                local_id=db_contact.id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "contact creation")

    async def get_contacts(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Any]:
        """Get contacts with optional search"""
        cache_key = f"contacts:{self.current_user.id}:{skip}:{limit}:{search}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        logger.info(f"Cache data : {cached}")
        if cached:
            return cached

        # Query from database
        stmt = select(ContactSchema)
        if search:
            stmt = stmt.where(
                ContactSchema.name.ilike(f"%{search}%")
                | ContactSchema.email.ilike(f"%{search}%")
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, contacts, expire=300)

        return contacts

    async def get_contact(self, contact_id: int) -> Optional[Any]:
        """Get specific contact by ID"""
        cache_key = f"contact:{contact_id}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database
        stmt = select(ContactSchema).where(ContactSchema.odoo_id == contact_id)
        result = await self.db.execute(stmt)
        contact = result.scalar_one_or_none()
        if contact:
            await self._cache_set(cache_key, contact, expire=300)

        return contact

    async def update_contact(
        self, contact_id: int, update_data: Dict[str, Any]
    ) -> SyncResponse:
        """Update contact and sync with Odoo"""
        try:
            # Get contact from database
            stmt = select(ContactSchema).where(ContactSchema.id == contact_id)
            result = await self.db.execute(stmt)
            contact = result.scalar_one_or_none()

            if not contact:
                return self._create_sync_response(
                    success=False,
                    message="Contact not found",
                    errors=["Contact not found"],
                )

            # Update local record
            for field, value in update_data.items():
                setattr(contact, field, value)

            await self.db.commit()

            # Sync with Odoo if Odoo ID exists
            if contact.odoo_id:
                odoo_client = await self._get_odoo_client()
                await odoo_client.update_contact(contact.odoo_id, update_data)

            # Clear cache
            await self._cache_delete(f"contact:{contact_id}")
            await self._cache_delete(f"contacts:{self.current_user.id}")

            self.logger.info(
                "Contact updated successfully",
                contact_id=contact_id,
                odoo_id=contact.odoo_id,
            )

            return self._create_sync_response(
                success=True,
                message="Contact updated and synced with Odoo",
                odoo_id=contact.odoo_id,
                local_id=contact_id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "contact update")

    async def sync_contacts_from_odoo(self, full: bool = False) -> SyncResponse:
        """Sync contacts from Odoo to local database"""
        try:
            domain = []
            if not full:
                stmt = select(func.max(ContactSchema.write_date))
                result = await self.db.execute(stmt)
                last_updated_date = result.scalar_one_or_none()
                if last_updated_date:
                    domain = [("write_date", ">", last_updated_date)]

            odoo_client = await self._get_odoo_client()
            odoo_contacts = await odoo_client.search_contacts(domain=domain)

            synced_count = 0
            for odoo_contact in odoo_contacts:
                stmt = select(ContactSchema).where(
                    ContactSchema.odoo_id == odoo_contact.id
                )
                result = await self.db.execute(stmt)
                existing_contact = result.scalar_one_or_none()
                if existing_contact:
                    # Update existing contact
                    for field, value in odoo_contact.model_dump(exclude=None).items():
                        self.logger.info(f"Update data, Key : {field}, Value : {value}")
                        if hasattr(existing_contact, field) and value:
                            setattr(existing_contact, field, value)
                else:
                    db_contact = ContactSchema(**odoo_contact.model_dump(exclude=None))
                    db_contact.id = None
                    db_contact.odoo_id = odoo_contact.id
                    db_contact.user_id = self.current_user.id
                    self.db.add(db_contact)
                    self.db.add(odoo_contact)
                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"contacts:{self.current_user.id}")
            self.logger.info("Contacts synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} contacts from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "contact sync from Odoo")
