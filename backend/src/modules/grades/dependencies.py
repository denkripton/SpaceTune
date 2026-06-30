from fastapi import Depends

from src.modules.auth import user_repository
from src.modules.auth.repository import UserRepository
from src.modules.grades.service import GradeService
from src.modules.music.repository import TrackRepository
from src.modules.grades.repository import GradeRepository
from src.dependencies import RepoFactory


track_repository = RepoFactory(repo=TrackRepository)
grade_repository = RepoFactory(repo=GradeRepository)


class GradeServiceFactory:
    def __init__(self, service_cls: type[GradeService] = GradeService):
        self.service_cls = service_cls

    def create(
        self,
        track_repo: TrackRepository,
        user_repo: UserRepository,
        grade_repo: GradeRepository,
    ) -> GradeService:
        return self.service_cls(
            track_repo=track_repo,
            user_repo=user_repo,
            grade_repo=grade_repo,
        )


grade_service_factory = GradeServiceFactory()


def get_grade_service(
    track_repo: TrackRepository = Depends(track_repository),
    user_repo: UserRepository = Depends(user_repository),
    grade_repo: GradeRepository = Depends(grade_repository),
) -> GradeService:
    return grade_service_factory.create(
        track_repo=track_repo,
        user_repo=user_repo,
        grade_repo=grade_repo,
    )
