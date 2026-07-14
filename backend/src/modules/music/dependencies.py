from fastapi import Depends

from src.utils import UnitOfWork
from src.dependencies import RepoFactory, get_unit_of_work
from src.modules.auth import user_repository
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.repository import TrackRepository
from src.modules.music.service import TrackService

track_repository = RepoFactory(repo=TrackRepository)
grade_repository = RepoFactory(repo=GradeRepository)


class TrackServiceFactory:
    def __init__(self, service_cls: type[TrackService] = TrackService):
        self.service_cls = service_cls

    def create(
        self,
        track_repo: TrackRepository,
        user_repo: UserRepository,
        grade_repo: GradeRepository,
        uow: UnitOfWork,
    ) -> TrackService:
        return self.service_cls(
            track_repo=track_repo,
            user_repo=user_repo,
            grade_repo=grade_repo,
            uow=uow,
        )


track_service_factory = TrackServiceFactory()


def get_track_service(
    track_repo: TrackRepository = Depends(track_repository),
    user_repo: UserRepository = Depends(user_repository),
    grade_repo: GradeRepository = Depends(grade_repository),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TrackService:
    return track_service_factory.create(
        track_repo=track_repo,
        user_repo=user_repo,
        grade_repo=grade_repo,
        uow=uow,
    )
