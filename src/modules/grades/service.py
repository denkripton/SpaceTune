from src.modules.music.repository import TrackRepository
from src.modules.grades.repository import GradeRepository
from src.modules.auth.repository import UserRepository

from src.modules.music.config import logger
from src.exceptions import ServiceError


class GradeService:
    def __init__(
        self,
        track_repo: TrackRepository,
        user_repo: UserRepository,
        grade_repo: GradeRepository,
    ):
        self.__track_repo = track_repo
        self.__user_repo = user_repo
        self.__grade_repo = grade_repo

    async def grade_track(
        self, user_id, track_name: str, owner_name: str, user_grade: int
    ):
        existing_owner = await self.__user_repo.get_one(username=owner_name)

        if existing_owner is None:
            raise ServiceError(code=422, msg="User does not exist")

        existing_track = await self.__track_repo.get_one(
            name=track_name, owner_id=existing_owner.id
        )

        if existing_track is None:
            raise ServiceError(code=422, msg="Track does not exist")

        existing_grade = await self.__grade_repo.get_one(
            user_id=user_id, track_id=existing_track.id
        )

        if existing_grade is not None:
            existing_grade.grade = user_grade
            try:
                await self.__grade_repo.session.commit()
            except Exception as e:
                await self.__grade_repo.session.rollback()
                logger.warning(e)
            return f"You placed: {user_grade} to {track_name}, created by {existing_track.artists}"

        data = {
            "grade": user_grade,
            "user_id": user_id,
            "track_id": existing_track.id,
        }

        try:
            grade = await self.__grade_repo.create(**data)
            await self.__grade_repo.session.commit()
            await self.__grade_repo.session.refresh(grade)
        except Exception as e:
            await self.__grade_repo.session.rollback()
            logger.warning(e)

        return f"You placed: {user_grade} to {track_name}, created by {existing_track.artists}"
