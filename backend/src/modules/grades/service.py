from src.utils import UnitOfWork
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.config import logger
from src.modules.music.repository import TrackRepository
from src.utils.exceptions import ServiceError


class GradeService:
    def __init__(
        self,
        track_repo: TrackRepository,
        user_repo: UserRepository,
        grade_repo: GradeRepository,
        uow: UnitOfWork,
    ):
        self.__track_repo = track_repo
        self.__user_repo = user_repo
        self.__grade_repo = grade_repo
        self.__uow = uow

    async def grade_track(self, user_id, track_id, user_grade: int):
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        existing_track = await self.__track_repo.get_one(id=track_id)

        if existing_track is None:
            raise ServiceError(code=422, msg="Track does not exist")

        existing_grade = await self.__grade_repo.get_one(
            user_id=user_id, track_id=existing_track.id
        )

        if existing_grade is not None:
            existing_grade.grade = user_grade
            try:
                await self.__uow.commit()
            except Exception as e:
                await self.__uow.rollback()
                logger.warning(e)
                raise ServiceError(code=500, msg="Failed to update grade") from e
            return f"You placed: {user_grade} to {existing_track.name}, created by {existing_track.artists}"

        data = {
            "grade": user_grade,
            "user_id": user_id,
            "track_id": existing_track.id,
        }

        try:
            grade = await self.__grade_repo.create(**data)
            await self.__uow.commit(conflict_msg="You have already graded this track")
            await self.__uow.refresh(grade)
        except ServiceError:
            raise
        except Exception as e:
            await self.__uow.rollback()
            logger.warning(e)
            raise ServiceError(code=500, msg="Failed to update grade") from e

        return f"You placed: {user_grade} to {existing_track.name}, created by {existing_track.artists}"
