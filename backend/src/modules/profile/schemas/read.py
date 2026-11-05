import uuid
from datetime import date

from pydantic import EmailStr, Field

from src.utils.schemas.base_schema import BaseSchema


class ProfilePrivateReadSchema(BaseSchema):
    id: uuid.UUID
    username: str = Field(max_length=20, examples=["John Doe"])
    email: EmailStr = Field(max_length=50, examples=["johndoe@gmail.com"])
    photo_url: str | None = None
    birth_date: date | None = None
    bio: str | None = None
    country: str | None = None
    phone_number: str | None = None
    visible_fields: dict[str, bool] = Field(default_factory=dict)


class ProfilePublicReadSchema(BaseSchema):
    id: uuid.UUID
    username: str = Field(max_length=20, examples=["John Doe"])
    photo_url: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    bio: str | None = None
    country: str | None = None
    phone_number: str | None = None
