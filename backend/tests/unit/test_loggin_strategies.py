import pytest
from src.utils.logging.strategies import is_sensitive_key


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "user_password",
        "PasswordHash",
        "token",
        "access_token",
        "secret",
        "client_secret",
        "authorization",
        "cookie",
        "refresh_cookie",
        "api_key",
        "apikey",
        "X-Api-Key",
    ],
)
def test_flags_sensitive_keys(key):
    assert is_sensitive_key(key) is True


@pytest.mark.parametrize(
    "key",
    ["username", "email", "track_id", "duration", "request_id", "status_code"],
)
def test_does_not_flag_safe_keys(key):
    assert is_sensitive_key(key) is False


def test_custom_markers_replace_defaults():
    assert is_sensitive_key("custom_marker_field", markers=("custom_marker",)) is True
    assert is_sensitive_key("password", markers=("custom_marker",)) is False
