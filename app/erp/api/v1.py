from typing import List, cast
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status

from odoo.dependency import db
from odoo.dependency import odoo
from app.auth.auth import validate_token

from ..schema.customer_schema import Customer
from ..schema.product_schema import Product
from ..schema.sale_schema import Sale
from ..schema.session import Session
from ..schema.user import User

from ..controllers.customer_controller import CustomerController

from .rout_name import RouterName as Route

PREFIX = "/v1/projects"
TAG_NAME = "Projects"

mobile_router = APIRouter(
    prefix=PREFIX, tags=[TAG_NAME], dependencies=[Depends(validate_token)]
)

async def get_authz_token(request: Request) -> str:
    token = request.cookies.get("authz_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authz_token cookie",
        )
    return token


# Customer
@mobile_router.get(
    Route.customers,
    response_model=List[Customer],
    summary="Customer List",
    description="Use this function to request customer list in ERP.",
)
async def get_customers(
    login: str, session: str, token: str = Depends(get_authz_token)
):
    return await CustomerController.get_cust_from_cache_first(
        login=login, session=session, token=token, limit=100
    )


@mobile_router.get(
    Route.customer_check,
    response_model=List[Customer],
    summary="Customer",
    description="Use this function to check customer in ERP.",
)
async def customer_by_id(customer_id: str, token: str = Depends(get_authz_token)):
    return await CustomerController.get_cust_by_cust_id(
        customer_id=customer_id, token=token
    )
