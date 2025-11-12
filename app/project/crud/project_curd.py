import json
import logging
from datetime import datetime
from typing import List, Union

import asyncpg

from app.core.executor import prepare_and_fetch

_logger = logging.getLogger(__name__)


class PorjectCrud:
    def __init__(self, db_connection=None, odoo_connection=None) -> None:
        self.db_connection = db_connection
        self.odoo_connection = odoo_connection

    async def find_task(self, task_id: str) -> List[asyncpg.Record]:
        return await prepare_and_fetch(
            self.db_connection,
            "SELECT state,id FROM project_task WHERE id = $1;",
            task_id,
        )
