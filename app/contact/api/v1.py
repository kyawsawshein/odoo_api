"""Main API router for Odoo FastAPI integration"""

from typing import List, Optional

import structlog
from app.api.models.models import SyncResponse
from app.auth.api.v1 import get_current_user
from app.auth.models.models import User
from app.contact.services.contact_service import ContactService
from app.contact.models.model import Contact, ContactCreate, ContactUpdate
from app.contact.api.route_name import Route

# from app.kafka.producer import KafkaProducer
from app.core.database import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/contacts", tags=["Contacts"])


# Contact Endpoints
@router.post(Route.contact, response_model=SyncResponse)
async def create_contact(
    contact: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact and sync with Odoo"""
    service = ContactService(db, current_user)
    try:
        result = await service.create_contact(contact.dict())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}",
        )


@router.get(Route.contact, response_model=List[Contact])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get contacts with pagination and search"""
    service = ContactService(db, current_user)
    return await service.get_contacts(skip=skip, limit=limit, search=search)


@router.get(Route.contact_id, response_model=Contact)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific contact by ID"""
    service = ContactService(db, current_user)
    contact = await service.get_contact(contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    return contact


@router.put(Route.contact_id, response_model=SyncResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update contact and sync with Odoo"""
    service = ContactService(db, current_user)
    try:
        result = await service.update_contact(
            contact_id, contact.dict(exclude_unset=True)
        )
        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     KafkaProducer.send_message,
        #     "odoo-contacts",
        #     {
        #         "action": "update",
        #         "user_id": current_user.id,
        #         "contact_id": contact_id,
        #         "update_data": contact.dict(exclude_unset=True)
        #     }
        # )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}",
        )


# @router.post(Route.contact_sync, response_model=SyncResponse)
# async def sync_contacts(
#     background_tasks: BackgroundTasks,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
#     full: bool = False,
# ):
#     """Sync Contact data with Odoo"""
#     service = ContactService(db, current_user)
#     try:
#         result = await service.sync_contacts_from_odoo(full)
#         # Send to Kafka for async processing
#         # background_tasks.add_task(
#         #     # KafkaProducer.send_message,
#         #     "odoo-contact",
#         #     {
#         #         "action": "sync",
#         #         "user_id": current_user.id
#         #     }
#         # )
#         return result
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to sync Contacts: {str(e)}",
#         )
