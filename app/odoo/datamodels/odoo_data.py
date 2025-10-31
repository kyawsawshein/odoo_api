from typing import Optional
from pydantic import BaseModel, model_validator


class Base(BaseModel):
    create_date: str
    write_date: str


class UomData(Base):
    id: int
    name: str


class CategoryData(Base):
    id: int
    name: str


class CurrencyData(Base):
    id: int
    name: str
    symbol: str


class ContactData(Base):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

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


class ProductData(Base):
    id: int
    name: str
    default_code: Optional[str] = None
    list_price: Optional[float] = 0.0
    standard_price: Optional[float] = 0.0

    @model_validator(mode="before")
    @classmethod
    def check_total(cls, values):
        default_code = values.get("default_code")
        # convert boolean False or True to None
        if isinstance(default_code, bool):
            values["default_code"] = None

        return values
