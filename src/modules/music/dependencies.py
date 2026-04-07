from fastapi import Depends

from src.modules.auth import user_repository
from src.modules.auth.repositories.user import UserRepository
from src.modules.music.service import TrackService
from src.modules.music.repositories.track import TrackRepository
from src.modules.music.repositories.grade import GradeRepository
from src.dependencies import RepoFactory


track_repository = RepoFactory(repo=TrackRepository)
grade_repository = RepoFactory(repo=GradeRepository)


class TrackServiceFactory:
    def __call__(
        self,
        track_repo: TrackRepository = Depends(track_repository),
        user_repo: UserRepository = Depends(user_repository),
        grade_repo: GradeRepository = Depends(grade_repository),
    ):

        service = TrackService(
            track_repo=track_repo, user_repo=user_repo, grade_repo=grade_repo
        )
        return service


get_track_service = TrackServiceFactory()
