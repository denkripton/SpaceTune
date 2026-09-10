
from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class User409(ExceptionSchema):
    detail: str | dict = Field(
        ..., examples=["User already exists"]
    )
