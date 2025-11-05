from pydantic import BaseModel


class CustomerRequestFilter(BaseModel):
    limit: int = 50


class Customer(BaseModel):
    id: int
    customer_id: str
    name: str
    personal_mobile: str
