import re

from pydantic import field_validator, Field, ValidationInfo

from src.utils.schemas.base_schema import BaseSchema


class PasswordCreateSchema(BaseSchema):
    password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])
    confirm_password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        if not re.fullmatch(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,64}$",
            password,
        ):
            raise ValueError(
                """Password is invalid. It must contain at least: one lowercase letter, one upper case letter, one digit, one special character. Length: 8-64"""
            )
        return password

    @field_validator("confirm_password")
    def check_passwords(cls, conf_password: str, info: ValidationInfo):
        if conf_password != info.data["password"]:
            raise ValueError("Password confirmation is invalid")
        return conf_password