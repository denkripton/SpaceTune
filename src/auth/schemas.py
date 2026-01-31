from pydantic import BaseModel, field_validator, EmailStr, Field
from datetime import date
import uuid
import re



class UsersCreationSchema(BaseModel):
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        if not re.fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,64}$", password):
            raise ValueError("""Password is invalid. It must contain at least: one lowercase letter, one upper case letter, one digit, on special character. Length: 8-64""")
        return password


class UserReadSchema(BaseModel):
    id: uuid.UUID
    username: str = Field(max_length=20)
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])


class ProfileCreationSchema(BaseModel):
    birth_date: date
    bio: str


class UserProfileReadSchema(UserReadSchema, ProfileCreationSchema):
    pass
