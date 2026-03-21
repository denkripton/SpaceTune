from fastapi import Depends

from src.modules.auth.dependencies import user_repository
from src.modules.auth.repositories.user_repo import UserRepository
from src.modules.music.service import TrackService
from src.modules.music.repositories.track_repo import TrackRepository
from src.modules.music.repositories.rate_repo import RateRepository
from src.dependencies import RepoFactory


track_repository = RepoFactory(repo=TrackRepository)
rate_repository = RepoFactory(repo=RateRepository)


class TrackServiceFactory:
    def __call__(
        self,
        track_repo: TrackRepository = Depends(track_repository),
        user_repo: UserRepository = Depends(user_repository),
        rate_repo: RateRepository = Depends(rate_repository),
    ):

        service = TrackService(
            track_repo=track_repo, user_repo=user_repo, rate_repo=rate_repo
        )
        return service


get_track_service = TrackServiceFactory()
