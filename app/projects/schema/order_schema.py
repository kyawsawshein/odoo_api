from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectRequest(BaseModel):
    # poi_id : str = Field(alias="case_id", description="PreOrder Number in ERP.")
    # is_failover : bool = Field(description="Use to check done preorder for failover plan.")
    skip: int = 0
    limit: int = 100
    search: Optional[str] = None,

class OrderListResponse(BaseModel):
    data : List = []

class OrderData(BaseModel):
    poi : str
    order_type : str
    status : str
