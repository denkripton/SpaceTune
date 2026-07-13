from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.exceptions import ServiceError


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(
        self,
        conflict_msg: str = "Resource already exists or was modified concurrently",
    ) -> None:
        try:
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            raise ServiceError(code=422, msg=conflict_msg) from e

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, obj) -> None:
        await self._session.refresh(obj)

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()