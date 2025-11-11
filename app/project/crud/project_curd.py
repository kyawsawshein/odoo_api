import logging
from typing import Union, List
from datetime import datetime
import json
import asyncpg

from app.core.executor import prepare_and_fetch

_logger = logging.getLogger(__name__)

class PorjectCrud:
    def __init__(self, db_connection=None, odoo_connection=None) -> None:
        self.db_connection = db_connection
        self.odoo_connection = odoo_connection

    async def find_order(self, poi : str) ->List[asyncpg.Record]:
        return await prepare_and_fetch(self.db_connection, "SELECT state,id FROM frnt_order_order WHERE order_id = $1;", poi)
