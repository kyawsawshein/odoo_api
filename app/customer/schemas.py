from typing import List, Optional, Dict
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic.class_validators import validator


class CustomerOrderBy(str, Enum):
    ID = "id"
    CUSTOMER_ID = "customer_id"
    CREATE_DATE = "create_date"
    WRITE_DATE = "write_date"

class Customer(BaseModel):
    id: int
    name:         Optional[str]
    partner_code: Optional[str]
    customer_id:  Optional[str]
    mobile:       Optional[str]
    phone:        Optional[str]
    other_phone:  Optional[str]
    email:        Optional[str]
    employee_id:  Optional[str]
    nrc:          Optional[str]
    other_id:     Optional[str]
    passport:     Optional[str]

class CustomerResponse(BaseModel):
    data: List[Customer]

class CustomerFilter(BaseModel):
    nrc:         Optional[str]
    customer_id: Optional[str]
    employee_id: Optional[str]

    @validator("employee_id")
    @classmethod
    def validate_employee_id(cls, value, values):
        if not value:
            if not (values.get("nrc") or values.get("customer_id")):
                raise ValueError("At least one field (nrc or customer_id or employee_id) is required")
        return value

class NrcRequestParam(BaseModel):
    nrc_first_number_code: Optional[str] = Field(default=None, description="NRC First Number Code eg. '343716266287'")
    nrc_township_code: Optional[str] = Field(default=None, description="NRC Township Code eg. '043716266298'")
    nrc_register_code: Optional[str] = Field(default=None, description="NRC Register Code eg. 'f13716266775'")
    nrc_number: Optional[str] = Field(default=None, description="NRC Number eg. '009282'")

class PartnerInfoRequestParam(BaseModel):
    nationality_code: Optional[str] = Field(default=None, description="Nationality Code eg. 'db3716266085'")
    nrc: Optional[NrcRequestParam] = Field(default=None, description="NRC Info.")
    passport: Optional[str] = Field(default=None, description="Passport eg. 'MD20321'")
    other_id: Optional[str] = Field(defaul=None, description="Other ID eg. 'EOP09292'")

#pylint: disable=too-many-instance-attributes
class PersonalInfo(BaseModel):
    national_id: str
    is_nrc: Optional[bool]
    nrc_first_no_id: Optional[str]
    nrc_township_code_id: Optional[str]
    nrc_no: Optional[str]
    nrc_register_code: Optional[str]
    passport: Optional[str]
    nrc_type : Optional[str]
    other_id : Optional[str]

class PartnerResponseData(BaseModel):
    partner_code: str
    nrc: str

@dataclass
class NrcType:
    OTHER = "OTHER"
    STANDARD = "STANDARD"

class CustomerInfoApi(BaseModel):
    id           : str
    partner_code : str
    name         : Optional[str]
    customer_id  : Optional[str]
    full_nrc     : Optional[str]
    phone        : Optional[str]
    mobile       : Optional[str]
    other_phone  : Optional[str]
    active       : Optional[bool] = False
    is_company   : Optional[bool] = False
    external_company_id: Optional[str] = ""