
from pydantic import BaseModel


class ExceptionSchema(BaseModel):
    detail: str | dict
