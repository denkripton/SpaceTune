import respx
import httpx
import pytest
from httpx import ASGITransport

from src.api import api
from src.config import settings
from src.dependencies import get_session

pytestmark = pytest.mark.integration


@pytest.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    api.app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api.app.dependency_overrides.clear()


class TestOAuthRouterFlow:
    async def test_google_login_sets_state_cookie_and_redirects(self, client):
        response = await client.get("/users/oauth/google", follow_redirects=False)

        assert response.status_code == 307
        assert "accounts.google.com" in response.headers["location"]
        assert "state=" in response.headers["location"]

        assert "oauth_state" in response.cookies
        cookie_attrs = response.headers["set-cookie"]
        assert "HttpOnly" in cookie_attrs
        assert "SameSite=lax" in cookie_attrs or "SameSite=Lax" in cookie_attrs

    async def test_callback_rejects_missing_state_cookie(self, client):
        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "irrelevant", "state": "attacker-supplied-state"},
        )

        assert response.status_code == 422
        assert "Invalid or missing OAuth state" in response.text

    async def test_callback_rejects_mismatched_state(self, client):
        login_resp = await client.get("/users/oauth/google", follow_redirects=False)
        real_state = login_resp.cookies["oauth_state"]
        client.cookies.set("oauth_state", real_state)

        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "irrelevant", "state": "tampered-value"},
        )

        assert response.status_code == 422

    @respx.mock
    async def test_callback_succeeds_with_valid_state_and_mocks_google(self, client, monkeypatch):
        from src.modules.auth.services.oauth import OAuthService

        respx.post(OAuthService.GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(200, json={"access_token": "fake-google-token"})
        )
        respx.get(settings.GOOGLE_USERINFO_URL).mock(
            return_value=httpx.Response(
                200, json={"email": "newuser@test.com", "sub": "google-sub-id"}
            )
        )

        login_resp = await client.get("/users/oauth/google", follow_redirects=False)
        real_state = login_resp.cookies["oauth_state"]
        client.cookies.set("oauth_state", real_state)

        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "real-looking-code", "state": real_state},
        )

        assert response.status_code == 200
        assert "access" in response.json()
        assert "refresh" in response.json()
        assert response.cookies.get("oauth_state") is None