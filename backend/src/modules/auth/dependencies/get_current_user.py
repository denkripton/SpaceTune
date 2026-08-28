from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.modules.auth.dependencies.get_jwt import get_jwt_service
from src.modules.auth.utils import JWT
from src.utils.exceptions import UnauthorizedError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    jwt: JWT = Depends(get_jwt_service),
) -> str:
    token = credentials.credentials if credentials else None

    payload = jwt.validate_token(token)

    if payload is None:
        raise UnauthorizedError(msg="User not authorized")

    return payload["sub"]
