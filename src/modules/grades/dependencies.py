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
    def __call__(
        self,
        track_repo: TrackRepository = Depends(track_repository),
        user_repo: UserRepository = Depends(user_repository),
        grade_repo: GradeRepository = Depends(grade_repository),
    ):

        service = GradeService(
            track_repo=track_repo, user_repo=user_repo, grade_repo=grade_repo
        )
        return service


get_grade_service = GradeServiceFactory()
