import httpx
import pytest
from httpx import ASGITransport

from src.api import api
from src.modules.auth.dependencies import get_oauth_service
from src.utils.exceptions import ServiceError


class FakeOAuthService:
    def __init__(self, result=None, error: ServiceError | None = None):
        self._result = result
        self._error = error

    async def login(self, code, state, expected_state):
        if self._error is not None:
            raise self._error
        return self._result


class TestOAuthStateCleanupMiddleware:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", cookies={"oauth_state": "some-state"}
        ) as ac:
            yield ac
        api.app.dependency_overrides.clear()

    async def test_deletes_state_cookie_on_successful_callback(self, client):
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            result={"access": "a", "refresh": "r"}
        )

        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "x", "state": "matching"},
        )

        assert response.status_code == 200
        set_cookie_headers = response.headers.get_list("set-cookie")
        state_cookie_headers = [h for h in set_cookie_headers if h.startswith("oauth_state=")]
        assert state_cookie_headers, "expected a Set-Cookie header clearing oauth_state"
        assert "Max-Age=0" in state_cookie_headers[0] or "expires=" in state_cookie_headers[0].lower()

    async def test_deletes_state_cookie_when_login_rejects_with_service_error(self, client):
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            error=ServiceError(code=422, msg="Invalid or missing OAuth state")
        )

        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "x", "state": "attacker-state"},
        )

        assert response.status_code == 422
        set_cookie_headers = response.headers.get_list("set-cookie")
        state_cookie_headers = [h for h in set_cookie_headers if h.startswith("oauth_state=")]
        assert state_cookie_headers, "cookie must be cleared even on rejection"

    async def test_does_not_touch_cookies_on_unrelated_paths(self, client):
        response = await client.get("/users/me/profile")

        set_cookie_headers = response.headers.get_list("set-cookie")
        state_cookie_headers = [h for h in set_cookie_headers if h.startswith("oauth_state=")]
        assert state_cookie_headers == []