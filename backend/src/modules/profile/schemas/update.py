from datetime import date
from typing import Optional

from pydantic import Field

from src.utils.schemas.base_schema import BaseSchema


class ProfileUpdateSchema(BaseSchema):
    bio: Optional[str] = Field(default=None, max_length=1000)
    country: Optional[str] = Field(default=None, max_length=50, examples=["Ukraine"])
    phone_number: Optional[str] = Field(
        default=None, max_length=50, examples=["+380_99_999_9999"]
    )
    birth_date: Optional[date] = None