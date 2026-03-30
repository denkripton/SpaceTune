from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ProfileCreationSchema(BaseModel):
    birth_date: date
    bio: Optional[str]
    country: Optional[str] = Field(max_length=50)
    phone_number: Optional[str] = Field(max_length=50, examples=["+380_99_999_9999"])