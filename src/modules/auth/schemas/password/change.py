from pydantic import Field, ValidationInfo, field_validator

from src.modules.auth.utils import password_validation
from src.utils.schemas.base_schema import BaseSchema


class PasswordChangeSchema(BaseSchema):
    password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])
    new_password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])
    confirm_password: str = Field(min_length=8, max_length=64, examples=["som@Th1ng"])

    @field_validator("new_password")
    def validate_new_password(cls, new, info: ValidationInfo):
        password_validation(password=new)

        if "password" in info.data and new == info.data["password"]:
            raise ValueError("Password must be different")
        return new

    @field_validator("confirm_password")
    def check_passwords(cls, conf_password: str, info: ValidationInfo):
        if "new_password" in info.data and conf_password != info.data["new_password"]:
            raise ValueError("Password confirmation is invalid")
        return conf_password
