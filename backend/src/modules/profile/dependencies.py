from fastapi import Depends

from src.modules.profile.service import ProfileService
from src.modules.profile.repository import ProfileRepository
from src.modules.auth.repository import UserRepository
from src.dependencies import RepoFactory
from src.modules.auth.utils import JWT


user_repository = RepoFactory(repo=UserRepository)
profile_repository = RepoFactory(repo=ProfileRepository)



class ProfileServiceFactory:
    def __call__(
        self,
        user_repo: UserRepository = Depends(user_repository),
        profile_repo: ProfileRepository = Depends(profile_repository),
    ):
        return ProfileService(repo=user_repo, profile_repo=profile_repo)


get_profile_service = ProfileServiceFactory()
