"""Authentication router for FastAPI"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.models import OdooUserCredentials, Token, User, UserCreate
from app.auth.schemas import User as UserSchema
from app.auth.utils import (
    create_access_token,
    generate_api_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.core.database import get_db
from app.odoo.client import OdooClient
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserSchema:
    """Get current authenticated user"""
    token_data = verify_token(token)
    # Query user from database
    user = await db.get(UserSchema, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[UserSchema]:
    """Get current user if authenticated, otherwise return None"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        token_data = verify_token(token)

        # Query user from database
        user = await db.get(UserSchema, token_data.user_id)
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        # If any error occurs (invalid token, expired, etc.), return None
        return None


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login and get access token"""
    # Find user by username
    stmt = select(UserSchema).where(UserSchema.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check if username already exists
    stmt = select(UserSchema).where(UserSchema.username == user_data.username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    stmt = select(UserSchema).where(UserSchema.email == user_data.email)
    result = await db.execute(stmt)
    existing_email = result.scalar_one_or_none()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = UserSchema(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/odoo-login")
async def odoo_login(
    credentials: OdooUserCredentials,
    current_user: UserSchema = Depends(get_current_user),
):
    """Authenticate with Odoo and store session"""
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

        # Store Odoo session (implementation depends on your session storage)
        # This could be stored in Redis or database

        return {
            "message": "Odoo authentication successful",
            "odoo_uid": uid,
            "user_id": current_user.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo authentication failed: {str(e)}",
        )


@router.get("/me", response_model=User)
async def read_users_me(current_user: UserSchema = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/api-token")
async def create_api_token(
    name: str, scopes: list[str], current_user: UserSchema = Depends(get_current_user)
):
    """Create API token for external integrations"""
    api_token = generate_api_token(name, current_user.id, scopes)

    return {
        "name": name,
        "token": api_token,
        "scopes": scopes,
        "user_id": current_user.id,
    }
