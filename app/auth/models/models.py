"""Authentication models and schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT Token response model"""

    access_token: str
    token_type: str
    # expires_in: int


class TokenData(BaseModel):
    """Token payload data"""

    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: list[str] = []
    odoo_username: Optional[str] = None
    odoo_password: Optional[str] = None
    odoo_database: Optional[str] = None
    roles: list[str] = []


class UserBase(BaseModel):
    """Base user model"""
    id: int
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

    odoo_url: str
    odoo_database: str
    odoo_username: str
    odoo_password: str
    roles: list[str] = []

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


class OdooJWTLoginCredentials(BaseModel):
    """Odoo JWT login credentials"""

    login: str
    password: str
    # db: str
