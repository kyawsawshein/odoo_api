"""Pydantic models for API requests and responses"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class InventoryBase(BaseModel):
    """Base inventory model"""

    product_id: int = Field(..., description="Product ID")
    location_id: int = Field(..., description="Location ID")
    quantity: Decimal = Field(..., description="Quantity")
    lot_id: Optional[int] = Field(None, description="Lot/Serial number ID")


class InventoryCreate(InventoryBase):
    """Inventory creation model"""

    pass


class InventoryUpdate(BaseModel):
    """Inventory update model"""

    quantity: Optional[Decimal] = None
    location_id: Optional[int] = None


class Inventory(InventoryBase):
    """Inventory response model"""

    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
