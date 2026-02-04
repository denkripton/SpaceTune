from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.repository import UserRepository
from src.auth.models import User
from src.auth.utils.hash_generation import pw_manager


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data):
        data = data.model_dump()

        result = await self.session.execute(
            select(User).where(User.username == data["username"])
        )
        user = result.scalars().first()

        if user is not None:
            raise HTTPException(
                status_code=422, detail="User with this username already exists"
            )

        data["password"] = pw_manager.hash_password(data["password"])

        user = User(**data)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str):
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    async def get_by_username(self, username: str):
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user
