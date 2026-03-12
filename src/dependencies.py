from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from typing import Callable

from src.exceptions import Error
from src.config import logger
from src.databases.sql_db import AsyncSessionLocal


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_error(method: Callable, *args, **kwargs):
    try:
        return await method(*args, **kwargs)
    except Error as http_e:
        raise HTTPException(status_code=http_e.status_code, detail=http_e.message)
    except Exception as e:
        logger.critical(e)


class RepoFactory:
    def __init__(self, repo):
        self.repository_class = repo

    def __call__(self, session: AsyncSession = Depends(get_session)):
        return self.repository_class(session)
