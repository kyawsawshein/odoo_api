from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PaymentType(str, Enum):
    cash = "cash"
    bank = "bank"


class User(BaseModel):
    id: int
    login: str


class SaleResponse(BaseModel):
    success: bool = True
    sale_id: Optional[int]


class SaleLine(BaseModel):
    product_id: int
    price: float
    qty: int
    discount_perc: float


class Sale(BaseModel):
    login: str
    session_id: str
    customer_id: str
    personal_mobile: str
    tx_id: str
    tx_date: str
    synced: bool
    payment_type: str = Field(default=PaymentType.cash)
    lines: List[SaleLine]
