import logging
from fastapi import APIRouter, Depends

from odoo.dependency import odoo
from odoo.dependency import db
from app.auth.auth import validate_token
from odoo.core.default_responses import Message
from app.order.models.model import OrderResponse
from ..schema.order_schema import OrderRequest, OrderListResponse, OrderData
from ..controller import OrderController


_logger = logging.getLogger(__name__)

PREFIX = '/v1/order'
TAG_NAME = "Order"

router = APIRouter(
    prefix=PREFIX,
    tags=[TAG_NAME],
    dependencies=[Depends(validate_token)]
)
@router.post("/check/poi", response_model=OrderResponse, summary="Order Subscription", description="Use this function to verify order to add plan in ERP.")
async def check_order(request_para : OrderRequest, db_connection = Depends(db.connection), odoo_connection = Depends(odoo.connection)) -> OrderResponse:
    result = await OrderController.check_order(request_para, db_connection, odoo_connection)
    _logger.info("#check_order %s : %s" , request_para,result)
    return result

@router.post("/{poi_number}", response_model=Message, summary="Updte Order status", description="Use this funtion to update order's status in ERP.")
async def change_poi_status_to_done(poi_number: str, db_connection = Depends(db.connection), odoo_connection = Depends(odoo.connection)):
    return await OrderController.update_order(poi_number, db_connection, odoo_connection)

@router.get("/{poi}", response_model=OrderData, summary="Return Order details", description="Use this funtion to get order's data from ERP.")
async def get_order_data(poi: str, db_connection = Depends(db.connection)):
    return await OrderController.get_order(poi, db_connection)

@router.get("/", response_model=OrderListResponse, summary="Return Order details", description="Use this funtion to get order's data from ERP.")
async def get_order_data(filter: str, db_connection = Depends(db.connection)):
    return await OrderController.get_order_list(filter, db_connection)
