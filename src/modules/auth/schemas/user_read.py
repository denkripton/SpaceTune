import uuid

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: uuid.UUID
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
