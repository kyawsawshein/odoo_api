from typing import List, Any, Dict

from pydantic import BaseModel

from .authz_login_payload import OdooPayLoad


class Kwargs(BaseModel):
    domain: List[Any] = []
    fields: List[str]
    limit: int = 50


class Params(BaseModel):
    token: str
    args: List = []
    kwargs: Dict = {}


class RequestPayLoad(OdooPayLoad):
    params: Params


class PayLoadParams(BaseModel):
    token: str
    model: str
    func: str
    fields: List = []
    args: List = []
    domain: List = []
    limit: int = 50
