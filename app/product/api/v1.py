"""Frontend API router for project and task management with Odoo synchronization"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends

from app.api.models.models import SyncResponse
from app.auth.api.v1 import validate_token
from app.auth.session_auth import get_session_odoo_connection
from app.dependency import db
from app.product.api.route_name import Route
from app.product.controllers.product_controller import ProductController
from app.product.schemas.product import PricelistSchema, ProductSchema

logger = structlog.get_logger()


router = APIRouter(
    prefix="/product",
    tags=["Products"],
    dependencies=[Depends(validate_token)],
)


@router.get(Route.products, response_model=List[ProductSchema])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    write_date: Optional[str] = None,
    search: Optional[str] = None,
    odoo_connection=Depends(get_session_odoo_connection),
):
    """Get MRP orderd"""
    return await ProductController(odoo_connection).get_products(
        skip=skip, limit=limit, write_date=write_date, search=search
    )


@router.get(Route.pricelists, response_model=List[PricelistSchema])
async def get_pricelists(
    skip: int = 0,
    limit: int = 100,
    write_date: Optional[str] = None,
    search: Optional[str] = None,
    odoo_connection=Depends(get_session_odoo_connection),
):
    """Get specific task details from frontend"""
    return await ProductController(odoo_connection).get_pricelists(
        skip=skip, limit=limit, write_date=write_date, search=search
    )
