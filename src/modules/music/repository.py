from src.repositories.postgres import SQLAlchemyRepository
from src.modules.music.models import Track

import uuid

class TrackRepository(SQLAlchemyRepository):
    model = Track

    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self.get_one(owner_id=user_id)
        return user
