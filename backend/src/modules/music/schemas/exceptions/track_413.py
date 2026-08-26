from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Track413(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Audio file is too big", "Image file is too big"]
    )
