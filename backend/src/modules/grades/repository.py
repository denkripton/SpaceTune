import uuid
from typing import Iterable

from sqlalchemy import func, select

from src.modules.grades.models import Grade
from src.repositories import SQLAlchemyRepository


class GradeRepository(SQLAlchemyRepository):
    model = Grade

    async def get_user_by_id(self, owner_artist: uuid.UUID):
        artist = await self.get_one(owner_id=owner_artist)
        return artist

    async def get_aggregates_by_track_ids(
        self, track_ids: Iterable[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[float, int]]:
        track_ids = list(track_ids)
        if not track_ids:
            return {}

        query = (
            select(
                Grade.track_id,
                func.avg(Grade.grade).label("average_grade"),
                func.count(Grade.id).label("ratings_count"),
            )
            .where(Grade.track_id.in_(track_ids))
            .group_by(Grade.track_id)
        )
        result = await self.session.execute(query)

        return {
            row.track_id: (round(float(row.average_grade), 1), row.ratings_count)
            for row in result
        }
