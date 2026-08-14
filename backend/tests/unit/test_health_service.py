import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.modules.health.service import HealthService


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def health_service(mock_session):
    HealthService.clear_cache()
    return HealthService(session=mock_session)


async def test_check_returns_healthy_when_db_ping_succeeds(
    health_service, mock_session
):
    result = await health_service.check()

    mock_session.execute.assert_awaited_once()
    assert result.status == "healthy"
    assert result.database == "reachable"


async def test_check_returns_unhealthy_when_db_raises(health_service, mock_session):
    mock_session.execute = AsyncMock(side_effect=ConnectionRefusedError("no route"))

    result = await health_service.check()

    assert result.status == "unhealthy"
    assert result.database == "unreachable"


async def test_check_returns_unhealthy_when_db_ping_times_out(
    health_service, mock_session
):
    async def hang(*args, **kwargs):
        await asyncio.sleep(10)

    mock_session.execute = AsyncMock(side_effect=hang)

    result = await health_service.check()

    assert result.status == "unhealthy"
    assert result.database == "unreachable"


async def test_check_never_raises_regardless_of_db_error_type(
    health_service, mock_session
):
    mock_session.execute = AsyncMock(side_effect=RuntimeError("unexpected"))

    result = await health_service.check()

    assert result.status == "unhealthy"
