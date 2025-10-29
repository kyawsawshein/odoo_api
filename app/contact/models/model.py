"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class ContactBase(BaseModel):
    """Base contact model"""

    name: str = Field(..., description="Contact name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    country_id: Optional[int] = Field(None, description="Country ID")
    is_company: bool = Field(False, description="Is company")
    company_type: Optional[str] = Field(None, description="Company type")


class ContactCreate(ContactBase):
    """Contact creation model"""

    pass


class ContactUpdate(BaseModel):
    """Contact update model"""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None


class Contact(ContactBase):
    """Contact response model"""

    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
