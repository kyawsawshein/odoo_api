"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Compoment(BaseModel):
    product_id: int = 0
    product_uom_qty: float = 0.0
    quantity: Optional[float] = 0.0
    uom: Optional[int] = 0


class WorkOrderSchema(BaseModel):
    id: int
    work_center_id: Optional[Dict] = None
    product_id: Optional[Dict] = None
    duration_expected: Optional[float] = None
    duration: Optional[float] = None
    status: str
    start_date: Optional[str] = None
    stop_date: Optional[str] = None


class MaterialCost(BaseModel):
    id: int
    name: str
    product_id: int
    planned_qty: float
    actual_qty: float
    uom_id: Optional[int] = None
    unit_cost: float
    total_cost: float
    actual_total_cost: float


class LabourCost(BaseModel):
    id: str
    name: str
    work_center_id: int
    planned_minute: float
    actual_minute: float
    unit_cost: float
    total_cost: float
    actual_total_cost: float


class OverheadCost(BaseModel):
    id: str
    name: str
    work_center_id: int
    planned_minute: float
    actual_minute: float
    unit_cost: float
    total_cost: float
    actual_total_cost: float


# Task (recursive, with dependencies)
class OrderSchema(BaseModel):
    id: int
    name: str
    product: Optional[Dict] = None
    status: str
    description: Optional[str] = None
    quantity: Optional[float] = 0.0
    uom: Optional[int] = None
    bon: Optional[int] = None
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    planned_start: Optional[str] = None
    planned_stop: Optional[str] = None
    source: Optional[List[str]] = None
    components_list: Optional[List[Compoment]] = None
    workorder_list: Optional[List[WorkOrderSchema]] = None
    material_cost_list: Optional[List[MaterialCost]] = None
    labour_cost_list: Optional[List[LabourCost]] = None
    overhead_cost_list: Optional[List[OverheadCost]] = None
    planned_start: Optional[str] = None
