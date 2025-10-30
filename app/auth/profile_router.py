"""User profile router for managing Odoo credentials"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.auth.models import OdooUserCredentials
from app.database import get_db
from app.odoo.client import OdooClient

logger = structlog.get_logger()

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/odoo-credentials", response_model=Optional[OdooUserCredentials])
async def get_odoo_credentials(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's Odoo credentials"""
    try:
        # Get user from database to get latest credentials
        stmt = select(UserSchema).where(UserSchema.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.odoo_url or not user.odoo_database:
            return None

        return OdooUserCredentials(
            odoo_username=user.odoo_username,
            odoo_password=user.odoo_password,
            odoo_database=user.odoo_database,
        )

    except Exception as e:
        logger.error(
            "Failed to get Odoo credentials", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Odoo credentials: {str(e)}",
        )


@router.post("/odoo-credentials", response_model=dict)
async def set_odoo_credentials(
    credentials: OdooUserCredentials,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set user's Odoo credentials and test connection"""
    try:
        # Test Odoo connection first
        odoo_client = OdooClient()

        # Use environment Odoo URL or default to common Odoo URL
        from app.config import settings

        odoo_url = settings.ODOO_URL or "http://localhost:8069"

        # Test authentication
        uid = await odoo_client.authenticate(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )

        # Update user with Odoo credentials
        stmt = select(UserSchema).where(UserSchema.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update credentials
        user.odoo_url = odoo_url
        user.odoo_database = credentials.odoo_database
        user.odoo_username = credentials.odoo_username
        user.odoo_password = credentials.odoo_password

        await db.commit()

        logger.info(
            "Odoo credentials updated successfully",
            user_id=current_user.id,
            odoo_database=credentials.odoo_database,
        )

        return {
            "message": "Odoo credentials updated successfully",
            "odoo_uid": uid,
            "odoo_url": odoo_url,
            "odoo_database": credentials.odoo_database,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to set Odoo credentials", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set Odoo credentials: {str(e)}",
        )


@router.delete("/odoo-credentials", response_model=dict)
async def delete_odoo_credentials(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete user's Odoo credentials"""
    try:
        # Get user from database
        stmt = select(UserSchema).where(UserSchema.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Clear Odoo credentials
        user.odoo_url = None
        user.odoo_database = None
        user.odoo_username = None
        user.odoo_password = None

        await db.commit()

        logger.info("Odoo credentials deleted", user_id=current_user.id)

        return {"message": "Odoo credentials deleted successfully"}

    except Exception as e:
        logger.error(
            "Failed to delete Odoo credentials", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Odoo credentials: {str(e)}",
        )


@router.post("/odoo-credentials/test", response_model=dict)
async def test_odoo_credentials(
    credentials: OdooUserCredentials,
    current_user: UserSchema = Depends(get_current_user),
):
    """Test Odoo credentials without saving them"""
    try:
        odoo_client = OdooClient()

        # Use environment Odoo URL or default to common Odoo URL
        from app.config import settings

        odoo_url = settings.ODOO_URL or "http://localhost:8069"

        # Test authentication
        uid = await odoo_client.authenticate(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )

        # Test basic operations
        contact_count = await odoo_client.search_contacts(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        product_count = await odoo_client.search_products(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        logger.info(
            "Odoo credentials test successful",
            user_id=current_user.id,
            odoo_uid=uid,
            contact_count=len(contact_count),
            product_count=len(product_count),
        )

        return {
            "message": "Odoo credentials test successful",
            "odoo_uid": uid,
            "contact_count": len(contact_count),
            "product_count": len(product_count),
            "odoo_url": odoo_url,
            "odoo_database": credentials.odoo_database,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Odoo credentials test failed", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo credentials test failed: {str(e)}",
        )
