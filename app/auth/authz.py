# Implementation for API Client which is JWT AuthZ and JWT call to Odoo

from typing import cast, Dict, Any, List, Optional
from requests import request
from pydantic import BaseModel

from app.config import settings
# from app.erp_mobile.schema.authz_login_payload import Creds, LoginPayload
# from odoo.erp_mobile.schema.odoo_rpc_payload import (
#     RequestPayLoad,
#     Params,
#     PayLoadParams,
# )

from app.auth.authz_exception import (
    TokenExpiredError,
    InvalidCreds,
    InvalidToken,
    MissingCreds,
    APIClientError,
    APIUnexpectedResponseError,
    DataNotFound,
)

HEADERS = {"Content-Type": "application/json"}
POST = "POST"
JWT_EXPIRED = "ExpiredSignatureError"
ACCESS_DENIED = "AccessDenied"
VALIDATION_ERROR = "ValidationError"
INVALID_TOKEN = "InvalidTokenError"


class RKey:
    result = "result"
    token = "token"
    error = "error"
    data = "data"
    message = "message"
    debug = "debug"
    name = "name"

class Creds(BaseModel):
    login: str
    password: str


class LoginPayload(BaseModel):
    params: Creds

class PayLoadParams(BaseModel):
    domain: List
    fields: List
    limit: int


class Params(BaseModel):
    token: str
    args: List
    kwargs: Dict

class RequestPayLoad(BaseModel):
    params: Params

def _dispatch_token(response: Dict[str, Any]) -> Optional[str]:
    # Odoo always responds with a status code 200, even something is not correct
    # To handle this properly, the dispatcher steps in to check the response and
    # return with custom exception so that, controller can return correct status code—either 200 for success or 401 for unauthorized access.
    if RKey.result in response:
        result = cast(List[Dict[str, str]], response.get(RKey.result))
        token = cast(str, result[0].get(RKey.token))
        return token

    if RKey.error in response:
        error = response[RKey.error]
        data = error.get(RKey.data, {})

        # Handle JWT Expired error
        if JWT_EXPIRED in data.get(RKey.name, ""):
            raise TokenExpiredError("JWT token has expired.")

        if ACCESS_DENIED in data.get(RKey.name):
            raise InvalidCreds("Wrong Login or Password.")
        # Fallback for other known/unknown errors
        raise APIClientError(f"API Error: {data.get(RKey.debug)}")

    raise APIUnexpectedResponseError("Invalid response format")


async def get_authz_token(login: str, pwd: str) -> Optional[str]:
    url = f"{settings.ODOO_JWT_AUTHZ_HOST}{settings.ODOO_JWT_AUTHZ_LOGIN_EP}"
    print("#====== URL ", url, login, pwd)
    response = request(
        POST,
        url,
        headers=HEADERS,
        data=LoginPayload(params=Creds(login=login, password=pwd)).model_dump_json(),
        timeout=settings.ODOO_JWT_AUTHZ_TIMEOUT,
    )
    print("# response ", response)
    return _dispatch_token(response=response.json())


def _prep_kwargs(paras: PayLoadParams) -> Dict[str, Any]:
    kwargs = {}
    if paras.domain:
        kwargs.update(domain=paras.domain)
    if paras.fields:
        kwargs.update(fields=paras.fields)
    if paras.fields:
        kwargs.update(limit=paras.limit)

    return kwargs


def _dispatch_data(response: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    if response.get(RKey.result) or RKey.result in response:
        # result will be result = {} or result = [{}]
        if any(cast(List[Dict[str, Any]], response.get(RKey.result))):
            return cast(List[Dict[str, Any]], response.get(RKey.result))
        if not any(cast(List[Dict[str, Any]], response.get(RKey.result))):
            raise DataNotFound("Data not found.")

    if RKey.error in response:
        error = response[RKey.error]
        data = error.get(RKey.data, {})

        if VALIDATION_ERROR in data.get(RKey.name, ""):
            raise MissingCreds(f"API Error: {data.get(RKey.message)}")

        if JWT_EXPIRED in data.get(RKey.name, ""):
            raise TokenExpiredError("Token has expired")

        if INVALID_TOKEN in data.get(RKey.name, ""):
            raise InvalidToken("Invalid Token")
        # Fallback for other known/unknown errors
        raise APIClientError(f"API Error: {data.get(RKey.debug)}")

    raise APIUnexpectedResponseError("Invalid response format")


async def authz_call(paras: PayLoadParams) -> Optional[List[Dict[str, Any]]]:
    url = f"{settings.ODOO_JWT_AUTHZ_HOST}{settings.ODOO_JWT_AUTHZ_CALL_EP.format(model=paras.model, func=paras.func)}"
    response = request(
        POST,
        url,
        headers=HEADERS,
        data=RequestPayLoad(
            params=Params(
                token=paras.token,
                args=paras.args,
                kwargs=_prep_kwargs(paras=paras),
            )
        ).json(),
        timeout=settings.ODOO_JWT_AUTHZ_TIMEOUT,
    )
    return _dispatch_data(response=response.json())
