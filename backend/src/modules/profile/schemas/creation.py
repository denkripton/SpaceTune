from datetime import date

from pydantic import Field

from src.utils.schemas.base_schema import BaseSchema


class ProfileCreationSchema(BaseSchema):
    birth_date: date
    bio: str | None = Field(default=None, max_length=1000)
    country: str | None = Field(default=None, max_length=50, examples=["Ukraine"])
    phone_number: str | None = Field(
        default=None, max_length=50, examples=["+380_99_999_9999"]
    )