from fastapi import Depends

from src.dependencies import RepoFactory, get_unit_of_work
from src.modules.auth.repository import UserRepository
from src.modules.profile.repository import ProfileRepository
from src.modules.profile.service import ProfileService
from src.utils import UnitOfWork

user_repository = RepoFactory(repo=UserRepository)
profile_repository = RepoFactory(repo=ProfileRepository)


class ProfileServiceFactory:
    def __init__(self, service_cls: type[ProfileService] = ProfileService):
        self.service_cls = service_cls

    def create(
        self,
        user_repo: UserRepository,
        profile_repo: ProfileRepository,
        uow: UnitOfWork,
    ) -> ProfileService:
        return self.service_cls(
            repo=user_repo,
            profile_repo=profile_repo,
            uow=uow,
        )


profile_service_factory = ProfileServiceFactory()


def get_profile_service(
    user_repo: UserRepository = Depends(user_repository),
    profile_repo: ProfileRepository = Depends(profile_repository),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProfileService:
    return profile_service_factory.create(
        user_repo=user_repo,
        profile_repo=profile_repo,
        uow=uow,
    )
