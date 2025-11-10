"""Pydantic models for API requests and responses"""

from typing import List, Optional
from pydantic import BaseModel, Field

# from datetime import datetime, date
# from decimal import Decimal


class SyncResponse(BaseModel):
    """Synchronization response model"""

    success: bool
    message: str
    odoo_id: Optional[int] = None
    local_id: Optional[int] = None
    errors: List[str] = Field(default_factory=list)
