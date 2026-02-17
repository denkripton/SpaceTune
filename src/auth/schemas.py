from pydantic import BaseModel, field_validator, EmailStr, Field
from datetime import date
from typing import Optional, Union
import re
import uuid


class UserCreateSchema(BaseModel):
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        if not re.fullmatch(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,64}$",
            password,
        ):
            raise ValueError(
                """Password is invalid. It must contain at least: one lowercase letter, one upper case letter, one digit, on special character. Length: 8-64"""
            )
        return password


class UserRead(BaseModel):
    id: uuid.UUID
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])


class ProfileCreationSchema(BaseModel):
    birth_date: date
    bio: Optional[str]
    country: Optional[str] = Field(max_length=50)
    phone_number: Optional[str] = Field(max_length=50, examples=["+380_99_999_9999"])


class UserProfileReadSchema(ProfileCreationSchema, UserRead):
    pass


class UserUpdateSchema(BaseModel):
    username: str = Field(max_length=20)
    password: str = Field(min_length=8, max_length=64)


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
    password: str = Field(min_length=8, max_length=64)
