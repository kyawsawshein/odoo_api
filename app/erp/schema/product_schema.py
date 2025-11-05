from typing import Optional
from pydantic import BaseModel, Field


class ProductRequestFilter(BaseModel):
    limit: int = 50


class Product(BaseModel):
    id: int
    name: str
    list_price: Optional[float] = 0.0
