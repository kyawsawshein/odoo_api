from typing import List
from pydantic import ValidationError
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.asyncpg import paginate
from app.dependency import db, odoo
from app.auth.auth import validate_token
from ..crud import CustomerCRUD, BASE_QUERY_STRING
from ..schemas import Customer, CustomerFilter, CustomerResponse, PartnerInfoRequestParam, PartnerResponseData
from ..controller import CustomerController

router = APIRouter(
    prefix='/v1/customers',
    tags=["Customer"],
    dependencies=[Depends(validate_token)]
)

@router.get("/limit-offset", response_model=LimitOffsetPage[Customer])
async def get_customers_paginate(db_conn=Depends(db.connection)):
    return await paginate(db_conn, BASE_QUERY_STRING)

@router.get("", response_model=CustomerResponse)
async def get_customers(filters: str = Query(..., example=CustomerFilter().json()), db_conn = Depends(db.connection)):
    try:
        filter_data = CustomerFilter.parse_raw(filters)
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err.errors()) from err
    return await CustomerController.get_customer_by_filter(filter_data=filter_data, db_conn=db_conn)

@router.get("/{customer_id}", response_model=Customer)
async def get_customer_by_customer_id(customer_id: str, db_conn=Depends(db.connection)):
    """
    /v1/customers/{customer_id:str}
    """
    customer_manager = CustomerCRUD(db=db_conn)
    return await customer_manager.get_by_customer_id(customer_id=customer_id)


@router.post("/check", response_model=PartnerResponseData)
async def get_partner_code(request_para : PartnerInfoRequestParam, db_conn=Depends(db.connection),\
    odoo_conn=Depends(odoo.connection)):
    """
    /v1/customers/check
    """
    return await CustomerController.get_partner_code(partner_info=request_para,\
        db_conn=db_conn, odoo_conn=odoo_conn)
