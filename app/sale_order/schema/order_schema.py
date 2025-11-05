from typing import List
from pydantic import BaseModel, Field

from odoo_shared.frnt_order.datamodels.order_schema import OrderData

class OrderRequest(BaseModel):
    poi_id : str = Field(alias="case_id", description="PreOrder Number in ERP.")
    is_failover : bool = Field(description="Use to check done preorder for failover plan.")

class OrderListResponse(BaseModel):
    data : List[OrderData] = []

class OrderData(BaseModel):
    poi : str
    order_type : str
    status : str
