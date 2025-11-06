from typing import Union
from asyncpg import Connection
from odoo.core.query_executor import prepare_and_fetch, prepare_and_fetchrow
from odoo.core.param_parser import RestParams, prepare_query, COUNT_QUERY

from ..query import OrderQuery
from ..schema.order import OrderInfoApi

class OrderCRUD:
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    @classmethod
    async def get_billing_address(cls, address_id: int, db_conn: Connection) -> dict:
        return await prepare_and_fetchrow(db_conn, OrderQuery.DETAIL_BILLING_ADDRESS, address_id)

    @classmethod
    async def get_po_service_address(cls, poi: str, db_conn: Connection) -> dict:
        return await prepare_and_fetchrow(db_conn, OrderQuery.DETAIL_SERVICE_ADDRESS, poi)

    @classmethod
    async def get_order_detail(cls, poi: str, db_conn: Connection) -> Union[dict, None]:
        return await prepare_and_fetchrow(db_conn, OrderQuery.DETAIL_QUERY + OrderQuery.DETAIL_WHERE_CLAUSE, poi)

    @classmethod
    async def get_installation(cls, inst_id: int, db_conn: Connection) -> dict:
        return await prepare_and_fetchrow(db_conn, OrderQuery.DETAIL_INSTALLTION, inst_id)

    @classmethod
    async def get_orders_count(cls, rest_param: RestParams, filter_map: dict, db_conn: Connection):
        rest_param.range = None
        rest_param.sort = None
        query, query_args = prepare_query(query=f"{COUNT_QUERY} {OrderQuery.COMMON_QUERY}",\
            filter_map=filter_map, rest_param=rest_param)
        res = await prepare_and_fetchrow(db_conn, query, *query_args)
        return res.get('count')

    @classmethod
    async def get_orders(cls, rest_param: RestParams, filter_map: dict, db_conn: Connection):
        query, query_args = prepare_query(query=f"{OrderQuery.INFO_QUERY} {OrderQuery.COMMON_QUERY}",\
            filter_map=filter_map, rest_param=rest_param)
        records = await prepare_and_fetch(db_conn, query, *query_args)
        if records:
            return [ OrderInfoApi.parse_obj(tmp) for tmp in records ]
        return []
