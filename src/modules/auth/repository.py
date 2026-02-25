import uuid

from src.repositories.postgres import SQLAlchemyRepository
from src.modules.auth.models import User, UserProfile


class UserRepository(SQLAlchemyRepository):
    model = User

    async def get_by_email(self, email: str):
        user = await self.get_one(email=email)
        return user


class ProfileRepository(SQLAlchemyRepository):
    model = UserProfile

    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self.get_one(user_id=user_id)
        return user
