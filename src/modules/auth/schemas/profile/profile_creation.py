from datetime import date
from typing import Optional

from pydantic import Field

from src.utils.schemas.base_schema import BaseSchema


class ProfileCreationSchema(BaseSchema):
    birth_date: date
    bio: Optional[str]
    country: Optional[str] = Field(max_length=50, examples=["Ukraine"])
    phone_number: Optional[str] = Field(max_length=50, examples=["+380_99_999_9999"])