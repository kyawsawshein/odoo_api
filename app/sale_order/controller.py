from typing import Union
import json
from xmlrpc.client import Fault
import asyncpg
from fastapi import HTTPException, status

from odoo.core.default_responses import Message
from .crud.crud import ORDERCrud
from app.order.models.model import OrderResponse
from .schema.order_schema import OrderRequest, OrderListResponse, OrderData


class OrderController:

    @classmethod
    async def check_order(cls, para: Union[OrderSubscriptionRequest, OrderRequest], db_connection : asyncpg.connection, odoo_connection : asyncpg.connection) -> OrderResponse:
        if not await ORDERCrud(db_connection = db_connection, odoo_connection=odoo_connection).check_order_status(para):
            raise HTTPException(status_code=406, detail="Order Not Found.")
        return OrderResponse(message="Success")

    @classmethod
    async def update_order(cls, order : str, db_connection : asyncpg.connection, odoo_connection : asyncpg.connection) -> Message:
        result = await ORDERCrud(db_connection = db_connection, odoo_connection=odoo_connection).find_order(poi=order)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"POI Number [{order}] not found")
        if result[0][0] == OrderState.DONE.name:
            return Message(detail=f"POI [{order}] is already in done state")
        if result[0][0] != OrderState.PROCESSING.name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"POI is not in [{OrderState.PROCESSING.value}] state")

        try:
            odoo_connection.models.execute_kw(*odoo_connection.secrets, 'frnt_order.order','action_set_done', [[result[0][1]]])
        except Fault as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Code : {err.faultCode}, {err.faultString} (please check POI in ERP)"
            ) from err

        return Message(detail=f"POI [{order}] is successfully updated to done state")

    @classmethod
    async def get_order(cls, order : str, db_connection : asyncpg.connection) -> OrderData:
        try:
            result = await ORDERCrud(db_connection=db_connection).get_order_detail(poi=order)
        except Fault as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Code : {err.faultCode}, {err.faultString} (please check POI in ERP)"
            ) from err
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"POI Number [{order}] not found")

        return result

    @classmethod
    async def get_order_list(cls, filter: str, db_connection : asyncpg.connection) -> OrderListResponse:
        filter_dict = json.loads(filter)

        state = filter_dict.get("status")
        start_date = filter_dict.get("start_date")
        end_date = filter_dict.get("end_date")
        order_type = filter_dict.get("order_type")
        try:
            result = await ORDERCrud(db_connection=db_connection).get_order_list(state, start_date, end_date, order_type)
        except Fault as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Code : {err.faultCode}, {err.faultString} (please check POI in ERP)"
            ) from err

        return result
