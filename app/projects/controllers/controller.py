import json
from typing import Union
from xmlrpc.client import Fault

import asyncpg
from fastapi import HTTPException, status

from app.projects.models.model import OrderResponse

from ..crud.crud import ORDERCrud
from ..schema.order_schema import OrderData, OrderListResponse



class OrderController:
    def __init__(self) -> None:
        pass

    @classmethod
    async def check_order(
        cls,
        para: Union[str, str],
        db_connection: asyncpg.connection,
        odoo_connection: asyncpg.connection,
    ) -> OrderResponse:
        if not await ORDERCrud(
            db_connection=db_connection, odoo_connection=odoo_connection
        ).check_order_status(para):
            raise HTTPException(status_code=406, detail="Order Not Found.")
        return OrderResponse(message="Success")

    @classmethod
    async def get_order_list(
        cls, filter: str, db_connection: asyncpg.connection
    ) -> OrderListResponse:
        filter_dict = json.loads(filter)

        state = filter_dict.get("status")
        start_date = filter_dict.get("start_date")
        end_date = filter_dict.get("end_date")
        order_type = filter_dict.get("order_type")
        try:
            result = await ORDERCrud(db_connection=db_connection).get_order_list(
                state, start_date, end_date, order_type
            )
        except Fault as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Code : {err.faultCode}, {err.faultString} (please check POI in ERP)",
            ) from err

        return result
