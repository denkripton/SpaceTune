import asyncio
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.modules.health.enums import HealthCheckTimeout
from src.modules.health.schemas import HealthReadSchema


class HealthService:
    __cache_expires_at = 0.0
    __cached_result: HealthReadSchema | None = None

    def __init__(self, session: AsyncSession):
        self.__session = session

    @classmethod
    def clear_cache(cls) -> None:
        cls.__cache_expires_at = 0.0
        cls.__cached_result = None

    async def __ping_database(self) -> bool:
        try:
            async with asyncio.timeout(HealthCheckTimeout.DB_PING_SECONDS.value):
                await self.__session.execute(select(1))
            return True
        except Exception as e:
            logger.warning("Health check DB ping failed: %s", e)
            return False

    async def check(self) -> HealthReadSchema:
        now = time.monotonic()
        if self.__cached_result is not None and now < self.__cache_expires_at:
            return self.__cached_result

        database_ok = await self.__ping_database()

        if database_ok:
            status = "healthy"
            database = "reachable"
        else:
            status = "unhealthy"
            database = "unreachable"

        result = HealthReadSchema(status=status, database=database)
        self.__class__.__cached_result = result
        self.__class__.__cache_expires_at = (
            now + HealthCheckTimeout.CACHE_SECONDS.value
        )
        return result
