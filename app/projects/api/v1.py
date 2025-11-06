import logging
from fastapi import APIRouter, Depends

from typing import List, Dict
from app.dependency import odoo
from app.dependency import db
from app.auth.auth import validate_token

from app.projects.models.model import OrderResponse
from ..schema.order_schema import ProjectRequest
from ..controllers.controller import OrderController


_logger = logging.getLogger(__name__)

PREFIX = "/v1/projects"
TAG_NAME = "Projects"

router = APIRouter(
    prefix=PREFIX, tags=[TAG_NAME], dependencies=[Depends(validate_token)]
)


@router.post(
    "/project_dashboard",
    response_model=List[Dict],
    summary="Order Subscription",
    description="Use this function to verify order to add plan in ERP.",
)
async def check_order(
    request_para: ProjectRequest,
    db_connection=Depends(db.connection),
    odoo_connection=Depends(odoo.connection),
) -> OrderResponse:
    result = await OrderController.check_order(
        request_para, db_connection, odoo_connection
    )
    _logger.info("# Projects %s : %s", request_para, result)
    return result


# @router.get("/", response_model=OrderListResponse, summary="Return Order details", description="Use this funtion to get order's data from ERP.")
# async def get_order_data(filter: str, db_connection = Depends(db.connection)):
#     return await OrderController.get_order_list(filter, db_connection)
