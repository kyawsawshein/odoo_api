from typing import Callable, Coroutine, Any

from fastapi import HTTPException, status

# from odoo.core.default_responses import UnauthorizeCode, unauthorized_response

from app.auth.authz_exception import (
    MissingCreds,
    TokenExpiredError,
    DataNotFound,
    APIClientError,
    APIUnexpectedResponseError,
    InvalidToken,
    InvalidCreds,
)


def handle_odoo_exceptions(func: Callable[..., Coroutine[Any, Any, Any]]):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        # except MissingCreds as cred_err:
        #     raise unauthorized_response(
        #         code=UnauthorizeCode.FAILED_AUTH, mesg=str(cred_err)
        #     ) from cred_err
        except (TokenExpiredError, InvalidToken, InvalidCreds) as expired_err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(expired_err)
            ) from expired_err
        except DataNotFound as not_found_err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found_err)
            ) from not_found_err
        except (APIClientError, APIUnexpectedResponseError) as client_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(client_err),
            ) from client_err

    return wrapper
