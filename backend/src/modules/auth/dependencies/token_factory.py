from fastapi import Depends

from src.modules.auth.dependencies.get_jwt import get_jwt_service
from src.modules.auth.services import TokenService
from src.modules.auth.utils import JWT


class TokenServiceFactory:
    def __init__(self, service_cls: type[TokenService] = TokenService):
        self.service_cls = service_cls

    def create(self, jwt: JWT) -> TokenService:
        return self.service_cls(jwt=jwt)


token_service_factory = TokenServiceFactory()


def get_token_service(jwt: JWT = Depends(get_jwt_service)) -> TokenService:
    return token_service_factory.create(jwt=jwt)