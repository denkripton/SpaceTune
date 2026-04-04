import uuid

from pydantic import EmailStr, Field

from src.utils.schemas.base_schema import BaseSchema


class UserRead(BaseSchema):
    id: uuid.UUID
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
