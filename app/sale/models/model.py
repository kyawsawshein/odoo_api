"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class SaleOrderBase(BaseModel):
    """Base sale order model"""

    partner_id: int = Field(..., description="Customer ID")
    date_order: datetime = Field(..., description="Order date")
    order_line: List[Dict] = Field(default_factory=list, description="Order lines")


class SaleOrderCreate(SaleOrderBase):
    """Sale order creation model"""

    pass


class SaleOrder(SaleOrderBase):
    """Sale order response model"""

    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
