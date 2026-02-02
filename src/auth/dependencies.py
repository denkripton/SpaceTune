from fastapi import Depends

from src.auth.service import UserService
from src.auth.repository import UserRepository
from src.auth.repositories.postgres import PostgresUserRepository
from src.dependencies import get_session


async def get_user_repo(session=Depends(get_session)) -> UserRepository:
    return PostgresUserRepository(session)

async def get_user_service(repo: UserRepository = Depends(get_user_repo)):
    return UserService(repo)
