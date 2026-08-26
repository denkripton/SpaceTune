from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Track404(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Track does not exist"]
    )
