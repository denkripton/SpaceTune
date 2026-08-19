from fastapi import Depends

from src.dependencies import get_unit_of_work
from src.modules.auth.dependencies.get_jwt import get_jwt_service
from src.modules.auth.dependencies.user_repo import user_repository
from src.modules.auth.repository import UserRepository
from src.modules.auth.services import OAuthService
from src.modules.auth.utils import JWT
from src.utils import UnitOfWork


class OAuthServiceFactory:
    def __init__(self, service_cls: type[OAuthService] = OAuthService):
        self.service_cls = service_cls

    def create(
        self,
        user_repo: UserRepository,
        jwt: JWT,
        uow: UnitOfWork,
    ) -> OAuthService:
        return self.service_cls(repo=user_repo, jwt=jwt, uow=uow)


oauth_service_factory = OAuthServiceFactory()


def get_oauth_service(
    user_repo: UserRepository = Depends(user_repository),
    jwt: JWT = Depends(get_jwt_service),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> OAuthService:
    return oauth_service_factory.create(user_repo=user_repo, jwt=jwt, uow=uow)
