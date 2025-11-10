"""Pydantic models for API requests and responses"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date

# from decimal import Decimal


class SyncResponse(BaseModel):
    """Synchronization response model"""

    success: bool = False
    message: str
    errors: List[str] = Field(default_factory=list)


class OdooAuthResponse(SyncResponse):
    jwt_token: Optional[str] = None
    expires_in: Optional[int] = None
    odoo_user_id: Optional[int] = None
    odoo_username: Optional[str] = None
