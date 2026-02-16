from fastapi import Depends, Request, Response, HTTPException
from typing import Optional

from src.auth.service import UserService
from src.auth.repository import UserRepository, ProfileRepository
from src.repository import ABCRepository
from src.dependencies import get_session
from src.auth.utils.jwt import JWT


async def get_user_repo(session=Depends(get_session)) -> ABCRepository:
    return UserRepository(session)


async def get_profile_repo(session=Depends(get_session)) -> ABCRepository:
    return ProfileRepository(session)


def get_jwt_service() -> JWT:
    return JWT()


async def get_user_service(
    jwt: JWT = Depends(get_jwt_service),
    session=Depends(get_session),
):
    repo = UserRepository(session=session)
    profile_repo = ProfileRepository(session=session)
    return UserService(repo=repo, jwt=jwt, profile_repo=profile_repo)


async def get_current_user(
    request: Request, response: Response, jwt: JWT = Depends(get_jwt_service)
):
    auth_header: Optional[str] = request.headers.get("Authorization")
    token = auth_header.replace("Bearer", "") if auth_header else None

    payload = jwt.validate_token(token)

    if payload:
        return payload["sub"]

    get_refresh_token = request.cookies.get("refresh_token")
    refresh_token = jwt.validate_token(get_refresh_token)

    if refresh_token is None:
        raise HTTPException(status_code=401, detail="User not authorized")

    new_access_token = jwt.create_access_token(refresh_token["sub"])

    response.headers["X-New-Access-Token"] = new_access_token

    return refresh_token["sub"]
