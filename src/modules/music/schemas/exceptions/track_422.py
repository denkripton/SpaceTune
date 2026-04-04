from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Track422(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Track already exists or it doesn't exist"]
    )
