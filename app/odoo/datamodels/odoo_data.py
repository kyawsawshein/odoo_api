from typing import Optional
from pydantic import BaseModel, model_validator


class Contact(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    create_date: str
    write_date: str

    @model_validator(mode="before")
    @classmethod
    def check_total(cls, values):
        # convert boolean False or True to None
        default_code = values.get("email")
        if isinstance(default_code, bool):
            values["email"] = None

        default_code = values.get("phone")
        if isinstance(default_code, bool):
            values["phone"] = None

        return values


class Product(BaseModel):
    id: int
    name: str
    default_code: Optional[str] = None
    list_price: Optional[float] = 0.0
    standard_price: Optional[float] = 0.0
    create_date: str
    write_date: str

    @model_validator(mode="before")
    @classmethod
    def check_total(cls, values):
        default_code = values.get("default_code")
        # convert boolean False or True to None
        if isinstance(default_code, bool):
            values["default_code"] = None

        return values
