import uuid
from datetime import date
from typing import Optional

from pydantic import EmailStr, Field

from src.utils.schemas.base_schema import BaseSchema


class ProfilePrivateReadSchema(BaseSchema):
    id: uuid.UUID
    username: str = Field(max_length=20, examples=["John Doe"])
    email: EmailStr = Field(max_length=50, examples=["johndoe@gmail.com"])
    photo_url: Optional[str] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    visible_fields: dict[str, bool] = Field(default_factory=dict)


class ProfilePublicReadSchema(BaseSchema):
    id: uuid.UUID
    username: str = Field(max_length=20, examples=["John Doe"])
    photo_url: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
