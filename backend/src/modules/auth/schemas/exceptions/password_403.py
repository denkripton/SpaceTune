
from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Password403(ExceptionSchema):
    detail: str | dict = Field(
        ..., examples=["Incorrect password"]
    )