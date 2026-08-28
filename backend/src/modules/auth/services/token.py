from typing import Optional

from src.modules.auth.utils import JWT
from src.utils.exceptions import UnauthorizedError


class TokenService:
    def __init__(self, jwt: JWT):
        self.__jwt = jwt

    def create_token_pair(self, id: str) -> dict:
        access = self.__jwt.create_access_token(id)
        refresh = self.__jwt.create_refresh_token(id)
        return {
            "access": access,
            "refresh": refresh,
        }

    def refresh_access_token(self, refresh_token: Optional[str]) -> str:
        payload = self.__jwt.validate_refresh_token(refresh_token)

        if not payload:
            raise UnauthorizedError(msg="Invalid or expired refresh token")

        return self.__jwt.create_access_token(payload["sub"])

    def validate_access(self, token: Optional[str]) -> Optional[str]:
        payload = self.__jwt.validate_access_token(token)

        if not payload:
            return None

        return payload["sub"]