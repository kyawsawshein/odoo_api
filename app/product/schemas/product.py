"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CategorySchema(BaseModel):
    id: int
    name: str
    complete_name: str
    parent_id: Optional[Dict] = None


class PricelistSchema(BaseModel):
    id: int
    name: str
    product_id: Optional[int] = None
    default_code: Optional[str] = None
    product_tmpl_id: Optional[int] = None
    fixed_price: Optional[float] = None
    percent_price: Optional[float] = None
    price_surcharge: Optional[float] = None
    price_discount: Optional[float] = None
    categ_id: Optional[int] = None
    categ_name: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    write_date: Optional[str] = None

# Task (recursive, with dependencies)
class ProductSchema(BaseModel):
    id: int
    product_tmpl_id: int
    name: str
    product_uom_id: int
    product_uom_name: str
    categ_id: int
    categ_name: str
    default_code: Optional[str] = None
    product_qty_available: Optional[float] = None
    barcode: Optional[str] = None
    list_price: Optional[float] = None
    cost_price: Optional[float] = None
    write_date: Optional[str] = None
