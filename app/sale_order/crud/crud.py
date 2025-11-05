import logging
from typing import Union, List
from datetime import datetime
import json
import asyncpg
from odoo_shared.frnt_order.datamodels.order_schema import OrderState, OrderSubscriptionRequest, OrderData

from odoo.core.query_executor import prepare_and_fetch
from ..query import OrderQuery
from ..schema.order_schema import OrderRequest, OrderListResponse

_logger = logging.getLogger(__name__)

class ORDERCrud:
    def __init__(self, db_connection=None, odoo_connection=None) -> None:
        self.db_connection = db_connection
        self.odoo_connection = odoo_connection

    async def check_order_status(self, para: Union[OrderSubscriptionRequest, OrderRequest]):
        if not para.is_failover:
            return await prepare_and_fetch(self.db_connection, "SELECT id FROM frnt_order_order WHERE order_id = $1 AND state = $2;", \
                *[para.poi_id, OrderState.PROCESSING.name])
        return await prepare_and_fetch(self.db_connection, "SELECT id FROM frnt_order_order WHERE order_id = $1 AND state = any($2);", \
            *[para.poi_id, [OrderState.PENDING_COMPLETE.name, OrderState.DONE.name]])

    async def find_order(self, poi : str) ->List[asyncpg.Record]:
        return await prepare_and_fetch(self.db_connection, "SELECT state,id FROM frnt_order_order WHERE order_id = $1;", poi)

    async def update_order(self, poi : str, state : OrderState) -> None:
        return await prepare_and_fetch(self.db_connection, "UPDATE frnt_order_order SET state = $1 WHERE order_id = $2;", *[state.name, poi])

    async def get_order_detail(self, poi: str) -> OrderData:
        await self.db_connection.prepare(OrderQuery.ORDER_QUERY)
        result = await self.db_connection.fetch(OrderQuery.ORDER_QUERY, poi)
        if not result:
            return False
        return OrderData.parse_obj(json.loads(result[0][0]))

    async def get_order_list(self, state: str, start_date: str, end_date: str, order_type: str) -> OrderListResponse:
        await self.db_connection.prepare(OrderQuery.ORDER_LIST_QUERY)
        result = await self.db_connection.fetch(OrderQuery.ORDER_LIST_QUERY, state, order_type, datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d'))
        if not result:
            return OrderListResponse()
        return OrderListResponse(data=[OrderData.parse_obj(json.loads(order[0]))for order in result])
