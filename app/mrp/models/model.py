"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator


class User(BaseModel):
    id: int
    name: str


class Model(BaseModel):
    id: int
    name: str


class Component(BaseModel):
    product_id: int
    product_uom_qty: float
    product_uom: Optional[int] = None


class WorkOrder(BaseModel):
    id: int
    name: str
    production_id: Model
    product_id: Model
    duration_expected: Optional[float] = None
    workcenter_id: Model
    state: str

    @field_validator("production_id", "product_id", "workcenter_id", mode="before")
    @classmethod
    def _parse_model_fields(cls, v):
        if not v:
            return v
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return {"id": v[0], "name": v[1]}
        if isinstance(v, dict):
            return v
        raise ValueError("Invalid format for model field")


class MaterialCost(BaseModel):
    product_id: int
    planned_qty: float


class LabourCost(BaseModel):
    id: int
    name: str
    workcenter_id: int
    planned_minute: Optional[float] = None


class OverheadCost(BaseModel):
    id: int
    name: str
    workcenter_id: int
    planned_minute: Optional[float] = None


class Order(BaseModel):
    id: int
    name: str
    product_id: Model
    product_qty: Optional[float] = None
    move_raw_ids: Optional[List] = None
    workorder_ids: Optional[List] = None
    material_cost_ids: Optional[List] = None
    labour_cost_ids: Optional[List] = None
    overhead_cost_ids: Optional[List] = None
    state: str

    @field_validator("product_id", mode="before")
    @classmethod
    def parse_product(cls, v):
        if isinstance(v, dict):
            return v
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return {"id": v[0], "name": v[1]}
        raise ValueError("Invalid product format")
