
from pydantic import Field

from src.utils.schemas.exception_schema import ExceptionSchema


class Profile413(ExceptionSchema):
    detail: str | dict = Field(
        ..., examples=["Photo file is too big"]
    )
