from typing import List, cast
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status

from odoo.dependency import db
from odoo.dependency import odoo
from app.auth.auth import validate_token
from odoo.core.config import settings as cfg

from ..schema.customer_schema import Customer
from ..schema.product_schema import Product
from ..schema.sale_schema import Sale
from ..schema.session import Session
from ..schema.user import User

from ..controllers.customer_controller import CustomerController
from ..controllers.product_controller import ProductController
from ..controllers.sale_controller import SaleController
from ..controllers.session import SessionController
from ..controllers.user import UserController

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


# Product
@mobile_router.get(
    Route.product,
    response_model=List[Product],
    summary="Product List",
    description="Use this function to request product list in ERP.",
)
async def get_products(login: str, session: str, token: str = Depends(get_authz_token)):
    return await ProductController.get_prod_from_cache_first(
        login=login, session_name=session, token=token
    )


# Session
@mobile_router.get(
    Route.session,
    response_model=Session,
    summary="Session ID",
    description="To get the session id for given sale user",
)
async def get_session_id(sale_user_id: str, token: str = Depends(get_authz_token)):
    return await SessionController.get_session(login=sale_user_id, token=token)


# Session Close
@mobile_router.post(
    Route.session_close,
    response_model=Session,
    summary="Session Close",
    description="To close session in ERP.",
)
async def close_session(session_id: str, token: str = Depends(get_authz_token)):
    return await SessionController.session_close(session_id=session_id, token=token)


# User
@mobile_router.get(
    Route.user,
    response_model=List[User],
    summary="User Login",
    description="To get the ERP login",
)
async def get_user(sale_user_id: str, token: str = Depends(get_authz_token)):
    return await UserController.get_user(login=sale_user_id, token=token)


# Sale
@mobile_router.post(
    Route.sales,
    summary="Sale Transacton",
    description="Use this function to create sale transaciont in ERP.",
)
async def sale(sale_tx: Sale, token: str = Depends(get_authz_token)):
    await SaleController.create_sale(data=sale_tx, token=token)
