# Route for Odoo Authz Token

from typing import cast
from fastapi import APIRouter, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from odoo.auth import BEARER_TOKEN_TYPE, Token

from odoo.core.config import settings
from odoo.erp_mobile.controllers.authz import authz_token

from ..schema.user import UserLogin

PREFIX = "/token"

authn_ck_router = APIRouter(prefix=PREFIX, tags=["Authorization"])


@authn_ck_router.post("/ck", description="This is fake call to set cookie for authn")
async def set_to_cookie(request: Request, response: Response):
    token = request.headers.get("Authorization")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.CK_MAX_AGE,
        path="/",
    )
    return {"message": "Login success"}
