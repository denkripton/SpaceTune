from src.modules.auth.utils.enums import PasswordValidationEnum


def password_validation(password):
    if not PasswordValidationEnum.REGEX.value().fullmatch(password):
        raise ValueError(
            "Password is invalid. It must contain at least: one lowercase letter, one upper case letter, one digit, one special character. Length: 8-64"
        )
    return password
