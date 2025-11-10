from enum import Enum
from pydantic import BaseModel
from fastapi import status
from .exceptions import CustomHTTPException


class Message(BaseModel):
    detail: str


class UnauthorizeCode(Enum):
    INVALID_SIG = 1
    INVALID_ISS = 2
    INVALID_AUD = 3
    INVALID_IAT = 4
    INVALID_EXP = 5
    INVALID_CLM = 6
    INVALID_JWT = 7
    FAILED_AUTH = 8


class UnauthorizedMessage(Message):
    status: int


def unauthorized_response(code: UnauthorizeCode, mesg: str):
    return CustomHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        obj=UnauthorizedMessage(status=code.value, detail=mesg),
        headers={"WWW-Authenticate": "Bearer"},
    )
