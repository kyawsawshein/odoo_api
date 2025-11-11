
import logging
from xmlrpc.client import ServerProxy
from typing import Any, List, Dict
from asyncpg import Connection
from pydantic import BaseModel
from fastapi import FastAPI, Request


# from odoo.core.config import settings
from app.core.logger import logger

# from odoo.core.exceptions import CustomHTTPException
from app.odoo.client import session_odoo_client

# _logger is now replaced by the simple logger instance

# Database
db = None
odoo = None


class Odoo(BaseModel):
    """Odoo"""

    secrets: tuple
    models: Any


class OdooAuthRequirements(BaseModel):
    """Odoo Authentication requireds"""

    url: str
    database: str
    user: str
    password: str


class ConfigureOdoo:
    """Conffigure Odoo"""

    def __init__(
        self,
        app: FastAPI,
        odoo_auth: OdooAuthRequirements,
        is_write_enable: bool = False,
    ) -> None:
        self.app = app
        self.uid = None
        self.odoo_auth = odoo_auth
        self.app.router.add_event_handler("startup", self._on_startup)

    async def _on_startup(self):
        common = ServerProxy(f"{self.odoo_auth.url}/xmlrpc/2/common")
        self.uid = common.authenticate(
            self.odoo_auth.database, self.odoo_auth.user, self.odoo_auth.password, {}
        )
        if not self.uid:
            raise Exception(
                f"Odoo Server [{self.odoo_auth.url}] User Login Failed"
            )  # pylint: disable=broad-exception-raised

    async def connection(self):
        yield Odoo(
            secrets=(self.odoo_auth.database, self.uid, self.odoo_auth.password),
            models=ServerProxy(f"{self.odoo_auth.url}/xmlrpc/2/object"),
        )


class SessionOdooConnection:
    """Session-based Odoo connection that uses cookies for authentication"""

    def __init__(self, odoo_auth: OdooAuthRequirements):
        self.odoo_auth = odoo_auth

    async def connection(self, request: Request):
        """Get Odoo connection using session (cookie) if available"""
        # Get user_id from cookie
        user_id = request.cookies.get("odoo_user_id")
        uid = int(user_id) if user_id else None

        # Return a wrapper that uses session-based authentication
        class SessionOdooWrapper:
            def __init__(self, odoo_auth, uid):
                self.odoo_auth = odoo_auth
                self.uid = uid

            async def execute_kw(
                self, model: str, method: str, args: List, kwargs: Dict = None
            ):
                return await session_odoo_client.execute_with_session(
                    self.odoo_auth.url,
                    self.odoo_auth.database,
                    self.odoo_auth.user,
                    self.odoo_auth.password,
                    self.uid,
                    model,
                    method,
                    args,
                    kwargs,
                )

        yield SessionOdooWrapper(self.odoo_auth, uid)


# Global session-based Odoo connection
session_odoo = None

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
