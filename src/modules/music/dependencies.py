from fastapi import Depends

from src.modules.auth.dependencies import user_repository
from src.modules.auth.repository import UserRepository

from src.modules.music.service import TrackService
from src.modules.music.repository import TrackRepository
from src.dependencies import RepoFactory


track_repository = RepoFactory(repo=TrackRepository)


class TrackServiceFactory:
    def __call__(
        self,
        track_repo: TrackRepository = Depends(track_repository),
        user_repo: UserRepository = Depends(user_repository),
    ):
        return TrackService(track_repo=track_repo, user_repo=user_repo)


get_track_service = TrackServiceFactory()
