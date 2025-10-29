"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class DeliveryBase(BaseModel):
    """Base delivery model"""

    partner_id: int = Field(..., description="Partner ID")
    picking_type_id: int = Field(..., description="Picking type ID")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    move_lines: List[Dict] = Field(default_factory=list, description="Move lines")


class DeliveryCreate(DeliveryBase):
    """Delivery creation model"""

    pass


class Delivery(DeliveryBase):
    """Delivery response model"""

    id: int
    odoo_id: Optional[int] = None
    state: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
