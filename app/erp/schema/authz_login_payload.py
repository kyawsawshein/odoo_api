from typing import Dict
from pydantic import BaseModel


class OdooRPCMethod:
    call = "call"


class OdooPayLoad(BaseModel):
    jsonrpc: str = "2.0"
    method: str = OdooRPCMethod.call


class Creds(BaseModel):
    login: str
    password: str


class LoginPayload(OdooPayLoad):
    params: Creds


# creds = Creds(login="login", password="pwd")
# res = LoginPayload(params=creds)
