# Implementation for Authorization Token for Odoo
from typing import Optional

from fastapi import APIRouter, Depends


from app.core.schemas import UnauthorizeCode, unauthorized_response
from app.auth.auth import validate_token
from app.auth.handle_exceptions import handle_odoo_exceptions

from app.auth.authz import get_authz_token
from ..schema.user import UserLogin

PREFIX = "/token/authz"

authz_router = APIRouter(
    prefix=PREFIX, tags=["Authorization"], dependencies=[Depends(validate_token)]
)


def _unauthorized_response():
    raise unauthorized_response(
        code=UnauthorizeCode.FAILED_AUTH, mesg="Incorrect username or password"
    )


@handle_odoo_exceptions
async def authz_token(user_login: UserLogin) -> Optional[str]:
    if not (user_login.username and user_login.password):
        return _unauthorized_response()

    return await get_authz_token(login=user_login.username, pwd=user_login.password)
