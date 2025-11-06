from typing import Optional
from pydantic import BaseModel


class RpcResponse(BaseModel):
    status: int = 200
    message: Optional[str] = "Successfully created."
    result: Optional[str] = "" #json string


class ApiResponse(BaseModel):
    result: str = 'Successful'
    status_code : int = 200
    message : str = ''

class APIResponse(BaseModel):
    success : bool = True
    message : str

class OrderResponse(APIResponse):
    pass
