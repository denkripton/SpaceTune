import httpx
import pytest
from httpx import ASGITransport

from src.api import api
from src.modules.auth.dependencies import get_oauth_service
from src.utils.exceptions import ServiceError


class FakeOAuthService:
    """
    Reuses the /users/oauth/google/callback route as a controllable trigger
    for each handler: it's the cheapest route in the app to make raise an
    arbitrary ServiceError or an unhandled Exception without touching a
    real DB session, since OAuthService is injected via DI and the route
    itself does no DB work before calling it.
    """

    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error

    async def login(self, code, state, expected_state):
        if self._error is not None:
            raise self._error
        return self._result


@pytest.fixture
async def client():
    transport = ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api.app.dependency_overrides.clear()


class TestServiceErrorHandler:
    async def test_service_error_response_has_rfc9457_shape(self, client):
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            error=ServiceError(code=422, msg="Invalid or missing OAuth state")
        )

        response = await client.get(
            "/users/oauth/google/callback",
            params={"code": "x", "state": "mismatched"},
        )

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        body = response.json()
        assert body["type"] == "https://spacetune.dev/errors/unprocessable-entity"
        assert body["title"] == "Unprocessable Entity"
        assert body["status"] == 422
        assert body["detail"] == "Invalid or missing OAuth state"
        assert body["instance"] == "/users/oauth/google/callback"

    async def test_service_error_type_and_title_vary_by_status_code(self, client):
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            error=ServiceError(code=409, msg="Already linked")
        )

        response = await client.get(
            "/users/oauth/google/callback", params={"code": "x", "state": "s"}
        )

        body = response.json()
        assert body["status"] == 409
        assert body["type"] == "https://spacetune.dev/errors/conflict"
        assert body["title"] == "Conflict"

    async def test_service_error_with_unmapped_status_falls_back_to_generic_type(
        self, client
    ):
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            error=ServiceError(code=418, msg="I'm a teapot")
        )

        response = await client.get(
            "/users/oauth/google/callback", params={"code": "x", "state": "s"}
        )

        body = response.json()
        assert body["status"] == 418
        assert body["type"] == "https://spacetune.dev/errors/error"
        assert body["title"] == "Error"
        assert body["detail"] == "I'm a teapot"


class TestUnhandledExceptionHandler:
    async def test_unexpected_exception_is_masked_as_generic_500_problem(self):
        # raise_app_exceptions=False: mirrors how a real ASGI server behaves
        # in production -- an unhandled exception becomes a 500 response,
        # not a Python exception propagating out of the client call. The
        # default (True) is meant for debugging app code during test writing,
        # not for asserting on the client-facing error response.
        transport = ASGITransport(app=api.app, raise_app_exceptions=False)
        api.app.dependency_overrides[get_oauth_service] = lambda: FakeOAuthService(
            error=RuntimeError("db connection dropped mid-transaction")
        )

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get(
                "/users/oauth/google/callback", params={"code": "x", "state": "s"}
            )
        api.app.dependency_overrides.clear()

        assert response.status_code == 500
        assert response.headers["content-type"] == "application/problem+json"

        body = response.json()
        assert body["type"] == "https://spacetune.dev/errors/internal-server-error"
        assert body["status"] == 500
        # Internal exception details must never leak to the client.
        assert "db connection dropped" not in body["detail"]
        assert body["detail"] == "Internal server error"


class TestValidationExceptionHandler:
    async def test_missing_required_field_returns_rfc9457_with_field_errors(
        self, client
    ):
        # /users/register requires username/email/password; omit them all.
        response = await client.post("/users/register", json={})

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        body = response.json()
        assert body["type"] == "https://spacetune.dev/errors/unprocessable-entity"
        assert body["status"] == 422
        assert body["instance"] == "/users/register"
        # Extension member: field-level breakdown must survive the
        # RFC 9457 wrapping, since bot/frontend need it for inline errors.
        assert isinstance(body["errors"], list)
        assert len(body["errors"]) >= 1
        assert any("email" in err["loc"] for err in body["errors"])


class TestHttpExceptionHandler:
    async def test_unknown_route_404_has_rfc9457_shape(self, client):
        response = await client.get("/this/route/does/not/exist")

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/problem+json"

        body = response.json()
        assert body["type"] == "https://spacetune.dev/errors/not-found"
        assert body["title"] == "Not Found"
        assert body["status"] == 404
        assert body["instance"] == "/this/route/does/not/exist"
