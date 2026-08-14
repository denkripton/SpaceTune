import uuid

import httpx
import pytest
import structlog
from httpx import ASGITransport
from src.api import api
from src.utils.middleware.constants import RequestContextHeaders
from src.utils.middleware.request_context import RequestContextMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

REQUEST_ID_HEADER = RequestContextHeaders.REQUEST_ID.value


@pytest.fixture
async def client():
    transport = ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api.app.dependency_overrides.clear()


@pytest.fixture
async def probe_client():
    captured = []

    async def endpoint(request):
        captured.append(dict(structlog.contextvars.get_contextvars()))
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/probe", endpoint)])
    app.add_middleware(RequestContextMiddleware)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, captured


async def test_generates_request_id_when_none_supplied(client):
    response = await client.get("/users/nonexistent/profile")

    request_id = response.headers.get(REQUEST_ID_HEADER)
    assert request_id is not None
    uuid.UUID(request_id)


async def test_echoes_client_supplied_request_id(client):
    supplied = str(uuid.uuid4())

    response = await client.get(
        "/users/nonexistent/profile",
        headers={REQUEST_ID_HEADER: supplied},
    )

    assert response.headers.get(REQUEST_ID_HEADER) == supplied


async def test_each_request_gets_a_distinct_id(client):
    first = await client.get("/users/nonexistent/profile")
    second = await client.get("/users/nonexistent/profile")

    assert first.headers[REQUEST_ID_HEADER] != second.headers[REQUEST_ID_HEADER]


async def test_binds_request_id_method_and_path_into_contextvars(probe_client):
    ac, captured = probe_client

    await ac.get("/probe")

    assert captured[0]["method"] == "GET"
    assert captured[0]["path"] == "/probe"
    uuid.UUID(captured[0]["request_id"])


async def test_contextvars_do_not_leak_between_sequential_requests(probe_client):
    ac, captured = probe_client

    await ac.get("/probe")
    await ac.get("/probe")

    assert captured[0]["request_id"] != captured[1]["request_id"]
