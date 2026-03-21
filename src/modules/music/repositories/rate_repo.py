import uuid

from src.repositories.postgres import SQLAlchemyRepository
from src.modules.music.models import Rate


class RateRepository(SQLAlchemyRepository):
    model = Rate

    async def get_user_by_id(self, owner_artist: uuid.UUID):
        artist = await self.get_one(owner_id=owner_artist)
        return artist
