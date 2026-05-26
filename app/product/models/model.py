"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator, model_validator


class ProductBase(BaseModel):

    @model_validator(mode="before")
    @classmethod
    def clean_values(cls, values):
        if isinstance(values, dict):
            for k, v in values.items():
                if v in [False, "", "False", "None"]:
                    values[k] = None
        return values


class Model(BaseModel):
    id: int
    name: str


class Category(BaseModel):
    id: int
    name: str
    complete_name: str
    parent_id: Model

    @field_validator("parent_id", mode="before")
    @classmethod
    def parse_model_fields(cls, v):
        if isinstance(v, dict):
            return v
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return {"id": v[0], "name": v[1]}
        raise ValueError("Invalid product format")


class Product(ProductBase):
    id: int
    product_tmpl_id: Model
    name: str
    uom_id: Model
    categ_id: Model
    write_date: str
    default_code: Optional[str] = None
    qty_available: Optional[float] = None
    barcode: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None

    @field_validator("product_tmpl_id", "uom_id", "categ_id", mode="before")
    @classmethod
    def parse_model_fields(cls, v):
        if isinstance(v, dict):
            return v
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return {"id": v[0], "name": v[1]}
        raise ValueError("Invalid product format")


class Pricelist(ProductBase):
    id: int
    pricelist_id: Model
    product_id: Optional[Model] = None
    product_tmpl_id: Optional[Model] = None
    categ_id: Optional[Model] = None
    fixed_price: Optional[float] = None
    percent_price: Optional[float] = None
    price_surcharge: Optional[float] = None
    price_discount: Optional[float] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    write_date: Optional[str] = None

    @field_validator(
        "pricelist_id", "product_id", "product_tmpl_id", "categ_id", mode="before"
    )
    @classmethod
    def _parse_model_fields(cls, v):
        if not v:
            return v
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return {"id": v[0], "name": v[1]}
        if isinstance(v, dict):
            return v
        raise ValueError("Invalid format for model field")
