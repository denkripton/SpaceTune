from datetime import UTC, datetime, timedelta

import httpx
import jwt as pyjwt
import pytest
from httpx import ASGITransport

from src.api import api
from src.config import settings
from src.modules.auth.utils import JWT

BASE_URL = "http://test"


@pytest.fixture
async def client():
    transport = ASGITransport(app=api.app)

    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


async def test_refresh_returns_only_new_access_token(client):
    jwt = JWT()
    old_refresh = jwt.create_refresh_token("user-123")
    client.cookies.set("refresh_token", old_refresh)

    response = await client.post("/users/refresh")

    assert response.status_code == 200
    body = response.json()
    assert list(body.keys()) == ["access"]

    payload = jwt.validate_access_token(body["access"])
    assert payload is not None
    assert payload["sub"] == "user-123"


async def test_refresh_rejects_missing_refresh_token(client):
    response = await client.post("/users/refresh")

    assert response.status_code == 401
    assert "Refresh token is missing" in response.text


async def test_refresh_rejects_expired_refresh_token(client):
    past = datetime.now(UTC) - timedelta(minutes=1)
    payload = {
        "sub": "user-123",
        "iat": int((past - timedelta(days=30)).timestamp()),
        "exp": int(past.timestamp()),
        "jti": "expired-jti",
        "type": "refresh",
    }
    expired = pyjwt.encode(
        payload, key=settings.JWT_SECRET_KEY, algorithm=JWT.algorithm
    )
    client.cookies.set("refresh_token", expired)

    response = await client.post("/users/refresh")

    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.text


async def test_refresh_rejects_access_token_used_as_refresh(client):
    jwt = JWT()
    access = jwt.create_access_token("user-123")
    client.cookies.set("refresh_token", access)

    response = await client.post("/users/refresh")

    assert response.status_code == 401