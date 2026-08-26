from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Profile404(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Profile does not exist"]
    )
