from typing import Union

from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Grade422(ExceptionSchema):
    detail: Union[str, dict] = Field(
        ..., examples=["You placed grade already"]
    )