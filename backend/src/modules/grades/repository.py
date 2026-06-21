import uuid

from src.repositories import SQLAlchemyRepository
from src.modules.grades.models import Grade


class GradeRepository(SQLAlchemyRepository):
    model = Grade

    async def get_user_by_id(self, owner_artist: uuid.UUID):
        artist = await self.get_one(owner_id=owner_artist)
        return artist
