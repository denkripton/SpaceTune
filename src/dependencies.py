from sqlalchemy.ext.asyncio import AsyncSession
from src.databases.sql_db import AsyncSessionLocal

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            session.close()
