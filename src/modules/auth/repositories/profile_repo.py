import uuid

from src.repositories.postgres import SQLAlchemyRepository
from src.modules.auth.models import UserProfile


class ProfileRepository(SQLAlchemyRepository):
    model = UserProfile

    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self.get_one(user_id=user_id)
        return user
