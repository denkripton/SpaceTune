from fastapi import Depends

from src.dependencies import get_unit_of_work
from src.modules.auth.dependencies.token_factory import get_token_service
from src.modules.auth.dependencies.user_repo import user_repository
from src.modules.auth.repository import UserRepository
from src.modules.auth.services import TokenService, UserService
from src.utils import UnitOfWork


class UserServiceFactory:
    def __init__(self, service_cls: type[UserService] = UserService):
        self.service_cls = service_cls

    def create(
        self,
        user_repo: UserRepository,
        token_service: TokenService,
        uow: UnitOfWork,
    ) -> UserService:
        return self.service_cls(repo=user_repo, token_service=token_service, uow=uow)


user_service_factory = UserServiceFactory()


def get_user_service(
    user_repo: UserRepository = Depends(user_repository),
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserService:
    return user_service_factory.create(
        user_repo=user_repo, token_service=token_service, uow=uow
    )
