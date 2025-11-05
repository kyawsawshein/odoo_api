from typing import List, Dict, Union
from asyncpg import Connection
from odoo.dependency import Odoo


class CallRPC:

    def __init__(
        self,
        model_name: str,
        method_name: str,
        db_connection: Connection = None,
        odoo_connection: Odoo = None,
    ):
        self.model = model_name
        self.method = method_name
        self.db_conn = db_connection
        self.odoo_conn = odoo_connection

    async def create_record(self, data: Union[List, Dict]):
        return self.odoo_conn.models.execute_kw(
            *self.odoo_conn.secrets, self.model, self.method, [data]
        )
