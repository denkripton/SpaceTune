from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Profile413(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Photo file is too big"]
    )
