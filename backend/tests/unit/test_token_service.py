from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import jwt as pyjwt
import pytest

from src.config import settings
from src.modules.auth.services.token import TokenService
from src.modules.auth.utils.jwt import JWT
from src.utils.exceptions import ServiceError


@pytest.fixture
def token_service():
    return TokenService(jwt=JWT())


@pytest.fixture
def real_jwt():
    return JWT()


def test_create_token_pair_delegates_both_token_types(token_service, real_jwt):
    result = token_service.create_token_pair(id="user-123")

    assert list(result.keys()) == ["access", "refresh"]

    access_payload = real_jwt.validate_access_token(result["access"])
    assert access_payload is not None
    assert access_payload["sub"] == "user-123"

    refresh_payload = real_jwt.validate_refresh_token(result["refresh"])
    assert refresh_payload is not None
    assert refresh_payload["sub"] == "user-123"


def test_refresh_access_token_returns_only_access_for_valid_refresh(
    token_service, real_jwt
):
    old_pair = token_service.create_token_pair(id="user-123")

    result = token_service.refresh_access_token(refresh_token=old_pair["refresh"])

    assert isinstance(result, str)

    payload = real_jwt.validate_access_token(result)
    assert payload is not None
    assert payload["sub"] == "user-123"


def test_refresh_access_token_mints_distinct_token(token_service):
    old_access = token_service.create_token_pair(id="user-123")["access"]

    result = token_service.refresh_access_token(
        refresh_token=token_service.create_token_pair(id="user-123")["refresh"]
    )

    assert result != old_access


def test_refresh_access_token_raises_401_for_missing_refresh_token(token_service):
    with pytest.raises(ServiceError) as exc_info:
        token_service.refresh_access_token(refresh_token=None)

    assert exc_info.value.status_code == 401


def test_refresh_access_token_raises_401_for_malformed_refresh_token(token_service):
    with pytest.raises(ServiceError) as exc_info:
        token_service.refresh_access_token(refresh_token="not.a.real.jwt.token")

    assert exc_info.value.status_code == 401


def test_refresh_access_token_raises_401_for_expired_refresh_token(token_service):
    past = datetime.now(UTC) - timedelta(minutes=1)
    payload = {
        "sub": "user-123",
        "iat": int((past - timedelta(days=30)).timestamp()),
        "exp": int(past.timestamp()),
        "type": "refresh",
    }
    expired_token = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )

    with pytest.raises(ServiceError) as exc_info:
        token_service.refresh_access_token(refresh_token=expired_token)

    assert exc_info.value.status_code == 401


def test_refresh_access_token_raises_401_when_access_token_used_as_refresh(
    token_service,
):
    access = token_service.create_token_pair(id="user-123")["access"]

    with pytest.raises(ServiceError) as exc_info:
        token_service.refresh_access_token(refresh_token=access)

    assert exc_info.value.status_code == 401


def test_validate_access_returns_sub_for_valid_access_token(token_service):
    pair = token_service.create_token_pair(id="user-123")

    assert token_service.validate_access(pair["access"]) == "user-123"


def test_validate_access_returns_none_for_missing_token(token_service):
    assert token_service.validate_access(None) is None


def test_validate_access_returns_none_when_refresh_token_used(token_service):
    pair = token_service.create_token_pair(id="user-123")

    assert token_service.validate_access(pair["refresh"]) is None


def test_validate_access_returns_none_for_expired_access_token(token_service):
    past = datetime.now(UTC) - timedelta(minutes=1)
    payload = {
        "sub": "user-123",
        "iat": int((past - timedelta(minutes=15)).timestamp()),
        "exp": int(past.timestamp()),
        "type": "access",
    }
    expired_token = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )

    assert token_service.validate_access(expired_token) is None


def test_create_token_pair_delegates_to_jwt_for_user_identifier():
    jwt = MagicMock()
    jwt.create_access_token = MagicMock(return_value="access-token")
    jwt.create_refresh_token = MagicMock(return_value="refresh-token")
    service = TokenService(jwt=jwt)

    result = service.create_token_pair(id="user-123")

    jwt.create_access_token.assert_called_once_with("user-123")
    jwt.create_refresh_token.assert_called_once_with("user-123")
    assert result == {"access": "access-token", "refresh": "refresh-token"}


def test_refresh_access_token_delegates_minting_to_jwt():
    jwt = MagicMock()
    jwt.validate_refresh_token = MagicMock(return_value={"sub": "user-123"})
    jwt.create_access_token = MagicMock(return_value="access-token")
    service = TokenService(jwt=jwt)

    result = service.refresh_access_token(refresh_token="refresh-token")

    jwt.validate_refresh_token.assert_called_once_with("refresh-token")
    jwt.create_access_token.assert_called_once_with("user-123")
    assert result == "access-token"