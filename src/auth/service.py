from fastapi import Response, HTTPException

from src.auth.schemas import UserCreateSchema, UserLoginSchema
from src.auth.repository import UserRepository
from src.auth.utils.jwt import JWT
from src.auth.utils.hash_generation import pw_manager


class UserService:
    def __init__(self, repo: UserRepository, jwt: JWT, response: Response):
        self.repo = repo
        self.jwt = jwt
        self.response = response

    async def register(self, data: UserCreateSchema):
        data = data.model_dump()

        existing_user = await self.repo.get_by_email(data["email"])

        if existing_user is not None:
            raise HTTPException(status_code=422, detail="User already exists")

        data["password"] = pw_manager.hash_password(data["password"])

        user = await self.repo.create(**data)

        await self.repo.session.commit()
        await self.repo.session.refresh(user)
        return user

    async def login(self, data: UserLoginSchema):
        user = await self.repo.get_by_email(data.email)

        if user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        password_check = pw_manager.check_password(data.password, user.password)
        user.id = str(user.id)

        if password_check is False:
            raise HTTPException(status_code=422, detail="Incorrect password")

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
