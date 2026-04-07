from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Profile422(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["Profile already exists or it doesn't exist"]
    )