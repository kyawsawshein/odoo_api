"""Main API router for Odoo FastAPI integration"""

import structlog
from app.api.models import SyncResponse
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.account.accounting_service import AccountingService
from app.account.models.currency import Currency
from app.account.route_name import Route

# from app.kafka.producer import KafkaProducer
from app.core.database import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get(Route.currencies, response_model=Currency)
async def get_currency(
    currency: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific contact by ID"""
    service = AccountingService(db, current_user)
    contact = await service.get_currency(currency)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    return contact


@router.post(Route.currencies_sync, response_model=SyncResponse)
async def sync_contacts(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    full: bool = False,
):
    """Sync Contact data with Odoo"""
    service = AccountingService(db, current_user)
    try:
        result = await service.sync_currency_from_odoo(full)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Contacts: {str(e)}",
        )
