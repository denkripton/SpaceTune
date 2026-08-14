import httpx
import pytest
from httpx import ASGITransport
from src.api import api
from src.modules.health.dependencies import get_health_service
from src.modules.health.schemas import HealthReadSchema


@pytest.fixture
async def client():
    transport = ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api.app.dependency_overrides.clear()


class _FakeHealthyService:
    async def check(self) -> HealthReadSchema:
        return HealthReadSchema(status="healthy", database="reachable")


async def test_health_returns_200_when_db_reachable(client):
    api.app.dependency_overrides[get_health_service] = _FakeHealthyService

    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] == "reachable"


class _FakeUnhealthyService:
    async def check(self) -> HealthReadSchema:
        return HealthReadSchema(status="unhealthy", database="unreachable")


async def test_health_returns_503_when_service_reports_unhealthy(client):
    api.app.dependency_overrides[get_health_service] = _FakeUnhealthyService

    response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
