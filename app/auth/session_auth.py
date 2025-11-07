"""Session-based Odoo authentication middleware"""

from typing import Optional

import structlog
from fastapi import Depends, HTTPException, Request, status

from app.auth.models.models import User
from app.config import settings
from app.odoo.client import session_odoo_client

logger = structlog.get_logger()


async def get_odoo_session_user(request: Request) -> Optional[User]:
    """
    Dependency to get the current authenticated user using session (cookie).
    Returns a User object with Odoo credentials if session is valid.
    """
    try:
        # Get user_id from cookie
        user_id_cookie = request.cookies.get("odoo_user_id")
        if not user_id_cookie:
            return None

        uid = int(user_id_cookie)

        # Get username from JWT token or other source
        # For now, we'll use the default Odoo credentials from settings
        # In a real implementation, you might want to store username in cookie too
        username = settings.ODOO_USERNAME

        # Create a User object representing the authenticated user
        user = User(
            id=uid,
            username=username,
            email=f"{username}@example.com",
            full_name=username,
            is_active=True,
            odoo_url=settings.ODOO_URL,
            odoo_database=settings.ODOO_DATABASE,
            odoo_username=username,
            odoo_password=settings.ODOO_PASSWORD,
            roles=[],
        )
        return user

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid user_id in cookie: {user_id_cookie}, error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in get_odoo_session_user: {e}")
        return None


async def require_odoo_session(
    current_user: Optional[User] = Depends(get_odoo_session_user),
) -> User:
    """
    Dependency that requires valid Odoo session authentication.
    Raises HTTPException if no valid session is found.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Odoo session authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return current_user


async def get_session_odoo_connection(request: Request):
    """
    Dependency that provides session-based Odoo connection.
    Uses user_id from cookie for authentication.
    """
    # Get user_id from cookie
    user_id_cookie = request.cookies.get("odoo_user_id")
    uid = int(user_id_cookie) if user_id_cookie else None

    # Return a wrapper that uses session-based authentication
    class SessionOdooConnection:
        def __init__(self, uid: Optional[int]):
            self.uid = uid

        async def execute_kw(
            self, model: str, method: str, args: list, kwargs: dict = None
        ):
            return await session_odoo_client.execute_with_session(
                settings.ODOO_URL,
                settings.ODOO_DATABASE,
                settings.ODOO_USERNAME,
                settings.ODOO_PASSWORD,
                self.uid,
                model,
                method,
                args,
                kwargs,
            )

    yield SessionOdooConnection(uid)
