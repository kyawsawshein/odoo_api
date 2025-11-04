"""Authentication router for FastAPI"""

from datetime import timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.models import (
    OdooJWTLoginCredentials,
    OdooUserCredentials,
    Token,
    User,
)
from app.auth.utils import (
    create_access_token,
    generate_api_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.config import settings
from app.core.database import get_db
from app.auth.auth import validate_token
from app.odoo.client import OdooClient
from app.auth.api.route_name import Route

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user using .env credentials"""
    token_data = verify_token(token)

    # Verify that the username from token matches APP_USER from .env
    if token_data.username != settings.APP_USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user credentials"
        )
    # Create a UserSchema object using credentials from .env
    user = User(
        id=token_data.user_id,
        username=settings.APP_USER,
        email=f"{settings.APP_USER}@example.com",
        full_name=settings.APP_USER,
        is_active=True,
        odoo_url=settings.ODOO_URL,
        odoo_database=settings.ODOO_DATABASE,
        odoo_username=settings.ODOO_USERNAME,
        odoo_password=settings.ODOO_PASSWORD,
    )

    return user


async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        token_data = verify_token(token)

        # Query user from database
        user = get_current_user()
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        # If any error occurs (invalid token, expired, etc.), return None
        return None

@router.post(Route.token, response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login and get access token using .env credentials"""
    # Verify username matches APP_USER from .env
    if form_data.username != settings.APP_USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password matches APP_PASSWORD from .env
    if not verify_password(form_data.password, settings.APP_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": settings.APP_USER, "user_id": 2},
        expires_delta=access_token_expires,
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


@router.post(Route.odoo_login)
async def odoo_login(
    credentials: OdooUserCredentials,
    current_user: User = Depends(get_current_user),
):
    """Authenticate with Odoo and get JWT token"""
    try:
        # Create Odoo client and authenticate
        odoo_client = OdooClient(
            url=settings.ODOO_URL,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )
        uid = await odoo_client.authenticate()
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": credentials.odoo_username, "user_id": uid},
            expires_delta=access_token_expires,
        )

        return {
            "message": "Odoo authentication successful",
            "user_id": current_user.id,
            "jwt_token": access_token,
            "expires_in": access_token_expires,
            "odoo_user_id": uid,
            "odoo_username": credentials.odoo_username,
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection to Odoo failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo authentication failed: {str(e)}",
        )


@router.get(Route.me, response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post(Route.odoo_jwt_login)
async def odoo_jwt_login(
    credentials: OdooJWTLoginCredentials,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """Authenticate with Odoo JWT endpoint and store token in cookie"""
    try:
        # Call Odoo JWT login endpoint
        jwt_url = f"{settings.ODOO_URL}/jwt/login"
        payload = {
            "login": credentials.login,
            "password": credentials.password,
            "db": credentials.db
        }
        print("URL : ", jwt_url, "Payload : ", payload)
        # Make request to Odoo JWT endpoint - try both json and data formats
        headers = {'Content-Type': 'application/json'}
        jwt_response = requests.post(jwt_url, json=payload, headers=headers)
        print("jwt response status: ", jwt_response.status_code)
        print("jwt response text: ", jwt_response.text)
        if jwt_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo JWT credentials",
            )

        # Extract JWT token from response
        jwt_data = jwt_response.json()
        jwt_token = jwt_data.get("token")

        if not jwt_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token received from Odoo JWT endpoint",
            )

        # Store JWT token in cookie
        response.set_cookie(
            key="odoo_jwt_token",
            value=jwt_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=24 * 60 * 60,  # 24 hours
        )

        return {
            "message": "Odoo JWT authentication successful",
            "login": credentials.login,
            "token_received": True,
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection to Odoo JWT endpoint failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo JWT authentication failed: {str(e)}",
        )


@router.post(Route.api_token)
async def create_api_token(
    name: str, scopes: list[str], current_user: User = Depends(get_current_user)
):
    """Create API token for external integrations"""
    api_token = generate_api_token(name, current_user.id, scopes)

    return {
        "name": name,
        "token": api_token,
        "scopes": scopes,
        "user_id": current_user.id,
    }
