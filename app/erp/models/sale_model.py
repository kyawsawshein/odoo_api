from typing import List
from dataclasses import dataclass


@dataclass
class SaleLineModel:
    product_id:int
    name: str
    product_uom_qyt: int
    price_unit : float


@dataclass
class SaleModel:
    partner_id:int
    date_order: str
    order_line: List[SaleLineModel]
