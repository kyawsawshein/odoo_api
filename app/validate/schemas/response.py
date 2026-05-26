"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ResponseSchema(BaseModel):
    id: int
    products: str
    complete_name: str
    parent_id: Optional[Dict] = None
