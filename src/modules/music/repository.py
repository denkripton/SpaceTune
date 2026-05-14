import uuid

from src.repositories import SQLAlchemyRepository
from src.modules.music.models import Track


class TrackRepository(SQLAlchemyRepository):
    model = Track

    async def get_track_by_owner(self, user_id: uuid.UUID):
        user = await self.get_one(owner_id=user_id)
        return user
