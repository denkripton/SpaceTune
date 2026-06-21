import pytest

from src.modules.auth.utils.password_validation import password_validation


@pytest.mark.parametrize(
    "valid_password",
    [
        "Som3Th!ng",
        "Aa1@aaaa",
        "A" * 60 + "a1!2",
        "P@ssw0rd123",
    ],
)
def test_password_validation_accepts_valid_passwords(valid_password):
    assert password_validation(valid_password) == valid_password


@pytest.mark.parametrize(
    ("invalid_password", "violated_rule"),
    [
        ("nouppercasenum1!", "no uppercase letter"),
        ("NOLOWERCASENUM1!", "no lowercase letter"),
        ("NoDigitsHere!!", "no digit"),
        ("NoSpecialChar123", "no special character"),
        ("Sh0rt!", "shorter than 8 characters"),
        ("A" * 70 + "a1!2", "longer than 64 characters"),
        ("", "empty string"),
    ],
)
def test_password_validation_rejects_invalid_passwords(invalid_password, violated_rule):
    with pytest.raises(ValueError):
        password_validation(invalid_password)
