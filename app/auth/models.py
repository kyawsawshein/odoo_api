"""Authentication models and schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT Token response model"""

    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""

    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: list[str] = []


class UserBase(BaseModel):
    """Base user model"""

    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model"""

    password: str


class UserUpdate(BaseModel):
    """User update model"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """User response model"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model for database"""

    hashed_password: str


class OdooUserCredentials(BaseModel):
    """Odoo user credentials for authentication"""

    odoo_username: str
    odoo_password: str
    odoo_database: str
