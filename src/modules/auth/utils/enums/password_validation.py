from enum import Enum

from src.modules.auth.utils.enums.constants import PASSWORD_REGEX

class PasswordValidationEnum(Enum):
    REGEX = PASSWORD_REGEX