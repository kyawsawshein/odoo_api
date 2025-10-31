"""Pydantic models for API requests and responses"""

from pydantic import BaseModel


class Currency(BaseModel):
    """Base currency model"""

    id: int
    name: str
    symbol: str
