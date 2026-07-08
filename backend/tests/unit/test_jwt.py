from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from src.modules.auth.utils.jwt import JWT
from src.config import settings


def test_jwt_module_imports_without_error():
    import importlib

    import src.modules.auth.utils.jwt as jwt_module

    importlib.reload(jwt_module)
    assert hasattr(jwt_module, "JWT")


@pytest.fixture
def jwt_service():
    return JWT()


def test_create_access_token_contains_correct_subject(jwt_service):
    token = jwt_service.create_access_token(id="user-123")
    payload = jwt_service.decode_token(token)

    assert payload["sub"] == "user-123"


def test_create_access_token_expires_in_fifteen_minutes(jwt_service):
    token = jwt_service.create_access_token(id="user-123")
    payload = jwt_service.decode_token(token)

    lifetime_seconds = payload["exp"] - payload["iat"]
    assert lifetime_seconds == 15 * 60


def test_create_refresh_token_expires_in_thirty_days_by_default(jwt_service):
    token = jwt_service.create_refresh_token(id="user-123")
    payload = jwt_service.decode_token(token)

    lifetime_seconds = payload["exp"] - payload["iat"]
    assert lifetime_seconds == 30 * 24 * 60 * 60


def test_create_refresh_token_respects_custom_expiration(jwt_service):
    now = datetime.now(UTC)
    custom_exp = int((now + timedelta(days=1)).timestamp())

    token = jwt_service.create_refresh_token(id="user-123", expiration=custom_exp)
    payload = jwt_service.decode_token(token)

    assert payload["exp"] == custom_exp


def test_validate_token_returns_none_for_empty_token(jwt_service):
    assert jwt_service.validate_token(None) is None
    assert jwt_service.validate_token("") is None


def test_validate_token_returns_none_for_malformed_token(jwt_service):
    assert jwt_service.validate_token("not.a.real.jwt.token") is None


def test_validate_token_returns_none_for_expired_token(jwt_service):
    past = datetime.now(UTC) - timedelta(minutes=1)
    payload = {
        "sub": "user-123",
        "iat": int((past - timedelta(minutes=15)).timestamp()),
        "exp": int(past.timestamp()),
    }
    expired_token = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )

    assert jwt_service.validate_token(expired_token) is None


def test_validate_token_returns_payload_for_valid_token(jwt_service):
    token = jwt_service.create_access_token(id="user-456")

    payload = jwt_service.validate_token(token)

    assert payload is not None
    assert payload["sub"] == "user-456"


def test_validate_token_returns_none_when_sub_claim_missing(jwt_service):
    now = datetime.now(UTC)
    payload = {
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    token_without_sub = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )

    assert jwt_service.validate_token(token_without_sub) is None


def test_validate_token_returns_none_when_sub_claim_is_empty_string(jwt_service):
    now = datetime.now(UTC)
    payload = {
        "sub": "",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    token_with_empty_sub = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )

    assert jwt_service.validate_token(token_with_empty_sub) is None