
from pydantic import EmailStr, Field, field_validator

from src.modules.auth.utils.password_validation import password_validation
from src.utils.schemas.base_schema import BaseSchema


class UserCreateSchema(BaseSchema):
    username: str = Field(max_length=20, examples=["John Doe"])
    email: EmailStr = Field(max_length=50, examples=["johndoe@gmail.com"])
    password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        return password_validation(password=password)