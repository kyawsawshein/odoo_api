from pydantic import BaseModel


class User(BaseModel):
    id: int
    login: str


class UserLogin(BaseModel):
    username: str
    password: str
