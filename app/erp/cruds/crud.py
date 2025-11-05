from typing import List
from asyncpg import Connection

from odoo.dependency import Odoo
from odoo.core.query_executor import prepare_and_fetch


class CRUD:
    def __init__(self, db_connection: Connection = None, odoo_connection: Odoo = None):
        self.db_connection = db_connection
        self.odoo_connection = odoo_connection

    async def get_data(self, query: str, query_args: List):
        return await prepare_and_fetch(self.db_connection, query, *query_args)


class UserCRUD(CRUD):
    async def get_login(self, query: str, query_args: List):
        return await prepare_and_fetch(self.db_connection, query, *query_args)


class CustomerCRUD(CRUD):
    async def get_customers(self, query: str, query_args: List):
        return await prepare_and_fetch(self.db_connection, query, *query_args)


class ProductCRUD(CRUD):
    async def get_products(self, query: str, query_param: List):
        return await prepare_and_fetch(self.db_connection, query, *query_param)


class SaleCRUD(CRUD):
    async def get_sale_id(self, query: str, query_param: List):
        return await prepare_and_fetch(self.db_connection, query, *query_param)
