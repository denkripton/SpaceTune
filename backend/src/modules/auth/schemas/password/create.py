import re

from pydantic import field_validator, Field, ValidationInfo

from src.utils.schemas.base_schema import BaseSchema
from src.modules.auth.utils.password_validation import password_validation

class PasswordCreateSchema(BaseSchema):
    password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])
    confirm_password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        return password_validation(password=password)

    @field_validator("confirm_password")
    def check_passwords(cls, conf_password: str, info: ValidationInfo):
        if conf_password != info.data["password"]:
            raise ValueError("Password confirmation is invalid")
        return conf_password