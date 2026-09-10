import uuid

from src.modules.profile.models import Profile
from src.repositories import SQLAlchemyRepository


class ProfileRepository(SQLAlchemyRepository):
    model = Profile

    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self.get_one(user_id=user_id)
        return user
