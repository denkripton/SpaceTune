from fastapi import Depends, Request, Response, HTTPException
from typing import Optional

from src.auth.service import UserService, AuthService
from src.auth.repository import UserRepository
from src.auth.repositories.postgres import PostgresUserRepository
from src.dependencies import get_session
from src.auth.utils.jwt import JWT


async def get_user_repo(session=Depends(get_session)) -> UserRepository:
    return PostgresUserRepository(session)


async def get_user_service(repo: UserRepository = Depends(get_user_repo)):
    return UserService(repo)


def get_jwt_service() -> JWT:
    return JWT()


async def get_auth_service(
    response: Response,
    repo: UserRepository = Depends(get_user_repo),
    jwt: JWT = Depends(get_jwt_service),
):
    return AuthService(repo=repo, jwt=jwt, response=response)


async def get_current_user(
    request: Request, response: Response, jwt: JWT = Depends(get_jwt_service)
):
    auth_header: Optional[str] = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header else None

    payload = jwt.validate_token(token)

    if payload:
        return payload["sub"]

    get_refresh_token = request.cookies.get("refresh_token")
    refresh_token = jwt.validate_token(get_refresh_token)

    if refresh_token is None:
        raise HTTPException(status_code=401)

    new_access_token = jwt.create_access_token(refresh_token["sub"])

    response.headers["X-New-Access-Token"] = new_access_token

    return refresh_token["sub"]
