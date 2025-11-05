# Route for Odoo Authz Token

from typing import cast
from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.auth import BEARER_TOKEN_TYPE, Token

from app.config import settings
from app.erp_mobile.controllers.authz import authz_token

from ..schema.user import UserLogin

PREFIX = "/token/authz"

authz_router = APIRouter(prefix=PREFIX, tags=["Authorization"])


@authz_router.post("/odoo", response_model=Token)
async def authz_token_odoo(form_data: OAuth2PasswordRequestForm = Depends()):
    return Token(
        access_token=cast(
            str,
            await authz_token(
                user_login=UserLogin(
                    username=form_data.username, password=form_data.password
                )
            ),
        ),
        token_type=BEARER_TOKEN_TYPE,
    )


@authz_router.post("/odoo/ck")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    response.set_cookie(
        key="authz_token",
        value=cast(
            str,
            await authz_token(
                user_login=UserLogin(
                    username=form_data.username, password=form_data.password
                )
            ),
        ),
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.CK_MAX_AGE,
        path="/",
    )
    return {"message": "Login success"}
