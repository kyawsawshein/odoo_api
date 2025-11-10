from pydantic import BaseModel


class CustomHTTPException(Exception):
    def __init__(
        self, *args: object, status_code: int, obj: BaseModel, headers: dict = None
    ) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.obj = obj
        self.headers = headers
