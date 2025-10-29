"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class PurchaseOrderBase(BaseModel):
    """Base purchase order model"""

    partner_id: int = Field(..., description="Supplier ID")
    currency_id: int
    date_order: datetime = Field(..., description="Order date")
    # order_line: List[Dict] = Field(default_factory=list, description="Order lines")


class PurchaseOrderLine(BaseModel):
    product_id: int
    product_qty: float
    product_uom_id: int
    price_unit: float
    tax_ids: list
    price_subtotal: float


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation model"""

    order_line: List[PurchaseOrderLine] = Field(
        default_factory=list, description="Order lines"
    )


class PurchaseOrder(PurchaseOrderBase):
    """Purchase order response model"""

    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

