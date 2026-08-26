from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class User404(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["User does not exist"]
    )
