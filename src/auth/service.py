from fastapi import Response, HTTPException

from src.auth.schemas import UserCreateSchema, UserLoginSchema
from src.auth.repository import UserRepository
from src.auth.utils.jwt import JWT
from src.auth.utils.hash_generation import pw_manager


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserCreateSchema):
        return await self.repo.create(data)


class AuthService:
    def __init__(self, repo: UserRepository, jwt: JWT, response: Response):
        self.repo = repo
        self.jwt = jwt
        self.response = response

    async def login(self, data: UserLoginSchema):
        user = await self.repo.get_by_email(data.email)

        password_check = pw_manager.check_password(data.password, user.password)
        user.id = str(user.id)

        if password_check is False:
            HTTPException(status_code=422, detail="Incorrect password")

        access = self.jwt.create_access_token(user.id)
        refresh = self.jwt.create_refresh_token(user.id)

        self.response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

        return {
            "access": access,
            "refresh": refresh,
        }
