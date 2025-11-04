import ast
import logging
from xmlrpc.client import ServerProxy
from typing import Any, List, Optional
from asyncpg import Connection
import requests
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.exception_handlers import http_exception_handler

# from odoo.core.config import settings
from app.core.logger import DEBUG_QUALNAME
# from odoo.core.exceptions import CustomHTTPException

_logger = logging.getLogger(DEBUG_QUALNAME)

# Database
db = None
odoo = None


class Odoo(BaseModel):
    secrets: tuple
    models: Any

class OdooAuthRequirements(BaseModel):
    url: str
    database: str
    user: str
    password: str

class ConfigureOdoo:
    def __init__(self, app: FastAPI, odoo_auth: OdooAuthRequirements, is_write_enable: bool = False) -> None:
        self.app = app
        self.uid = None
        self.odoo_auth = odoo_auth

        if is_write_enable:
            self.app.router.add_event_handler("startup", self._on_startup)

    async def _on_startup(self):
        common = ServerProxy(f'{self.odoo_auth.url}/xmlrpc/2/common')
        self.uid = common.authenticate(self.odoo_auth.database, self.odoo_auth.user, self.odoo_auth.password, {})
        if not self.uid:
            raise Exception(f"Odoo Server [{self.odoo_auth.url}] User Login Failed")#pylint: disable=broad-exception-raised

    async def connection(self):
        yield Odoo(
            secrets=(self.odoo_auth.database, self.uid, self.odoo_auth.password),
            models=ServerProxy(f'{self.odoo_auth.url}/xmlrpc/2/object')
            )

# async def exception_handler(request: Request, exc: CustomHTTPException):
#     _logger.warning("Status-Code: %s, Detail: %s", exc.status_code, exc.obj)
#     return JSONResponse(
#         status_code=exc.status_code,
#         content= exc.obj.dict() if isinstance(exc.obj, BaseModel) else exc.obj,
#         headers= exc.headers
#     )

# async def log_on_exception(request: Request, exc: HTTPException):
#     _logger.warning("Status-Code: %s, Detail: %s", exc.status_code, exc.detail)
#     return await http_exception_handler(request=request, exc=exc)

# def activate_exceptions(app: FastAPI) -> None:
#     app.add_exception_handler(CustomHTTPException, exception_handler)
#     app.add_exception_handler(HTTPException, log_on_exception)

