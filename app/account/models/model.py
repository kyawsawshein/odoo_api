
"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class AccountingMoveBase(BaseModel):
    """Base accounting move model"""

    journal_id: int = Field(..., description="Journal ID")
    # date: date = Field(..., description="Move date")
    ref: Optional[str] = Field(None, description="Reference")
    line_ids: List[Dict] = Field(default_factory=list, description="Move lines")


class AccountingMoveCreate(AccountingMoveBase):
    """Accounting move creation model"""

    pass


class AccountingMove(AccountingMoveBase):
    """Accounting move response model"""

    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
