"""User profile router for managing Odoo credentials"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.auth.router import get_current_user
from app.auth.utils import (
    create_access_token,
    generate_api_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.auth.schemas import User as UserSchema
from app.auth.models.models import OdooUserCredentials
from app.core.database import get_db
from app.odoo.client import OdooClient
from app.auth.route_name import Route
from app.config import settings


logger = structlog.get_logger()

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(Route.odoo_credentials, response_model=Optional[OdooUserCredentials])
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


@router.post(Route.odoo_credentials, response_model=dict)
async def set_odoo_credentials(
    credentials: OdooUserCredentials,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set user's Odoo credentials and test connection"""
    try:
        # Test Odoo connection first
        # Use environment Odoo URL or default to common Odoo URL
        odoo_url = settings.ODOO_URL or "http://localhost:8069"
        logger.info(f"odoo credentials : {odoo_url, credentials}")
        odoo_client = OdooClient(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        # Test authentication
        uid = await odoo_client.authenticate()
        logger.info(f"UID : {uid}")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )

        # Update user with Odoo credentials
        stmt = select(UserSchema).where(UserSchema.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        logger.info(f"User : {user}")
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


@router.delete(Route.odoo_credentials, response_model=dict)
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


@router.post(Route.odoo_credentials_test, response_model=dict)
async def test_odoo_credentials(
    credentials: OdooUserCredentials,
    current_user: UserSchema = Depends(get_current_user),
):
    """Test Odoo credentials without saving them"""
    try:
        # Use environment Odoo URL or default to common Odoo URL
        odoo_url = settings.ODOO_URL or "http://localhost:8069"
        logger.info(f"odoo credentials : {odoo_url, credentials}")

        odoo_client = OdooClient(
            url=odoo_url,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )

        # Test authentication
        uid = await odoo_client.authenticate()
        logger.info(f"User : {uid}")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )

        # Test basic operations
        contact_count = await odoo_client.search_contacts()
        product_count = await odoo_client.search_products()

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
