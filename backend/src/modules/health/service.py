import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger
from src.modules.health.constants import DB_PING_TIMEOUT_SECONDS
from src.modules.health.schemas import HealthReadSchema


class HealthService:
    def __init__(self, session: AsyncSession):
        self.__session = session

    async def __ping_database(self) -> bool:
        try:
            async with asyncio.timeout(DB_PING_TIMEOUT_SECONDS):
                await self.__session.execute(select(1))
            return True
        except Exception as e:
            logger.warning("Health check DB ping failed: %s", e)
            return False

    async def check(self) -> HealthReadSchema:
        database_ok = await self.__ping_database()

        if database_ok:
            status = "healthy"
            database = "connected"
        else:
            status = "unhealthy"
            database = "disconnected"

        return HealthReadSchema(status=status, database=database)
