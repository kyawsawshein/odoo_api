"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product model"""

    name: str = Field(..., description="Product name")
    default_code: Optional[str] = Field(None, description="Internal reference")
    list_price: Optional[Decimal] = Field(None, description="Sales price")
    standard_price: Optional[Decimal] = Field(None, description="Cost price")
    type: str = Field("product", description="Product type (product/consu/service)")
    categ_id: Optional[int] = Field(None, description="Category ID")
    uom_id: Optional[int] = Field(None, description="Unit of measure ID")
    description: Optional[str] = Field(None, description="Product description")


class ProductCreate(ProductBase):
    """Product creation model"""

    pass


class ProductUpdate(BaseModel):
    """Product update model"""

    name: Optional[str] = None
    default_code: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    description: Optional[str] = None


class Product(ProductBase):
    """Product response model"""

    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
