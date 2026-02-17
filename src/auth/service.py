from fastapi import HTTPException
import uuid

from src.auth.schemas import (
    UserCreateSchema,
    UserLoginSchema,
    ProfileCreationSchema,
    UserProfileReadSchema,
)
from src.auth.repository import UserRepository, ProfileRepository
from src.auth.utils.jwt import JWT
from src.auth.utils.hash_generation import pw_manager


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        profile_repo: ProfileRepository,
        jwt: JWT,
    ):
        self.profile_repo = profile_repo
        self.repo = repo
        self.jwt = jwt

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
        existing_user = await self.repo.get_by_email(data.email)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        password_check = pw_manager.check_password(
            data.password, existing_user.password
        )
        existing_user.id = str(existing_user.id)

        if password_check is False:
            raise HTTPException(status_code=422, detail="Incorrect password")

        access = self.jwt.create_access_token(existing_user.id)
        refresh = self.jwt.create_refresh_token(existing_user.id)

        return {
            "access": access,
            "refresh": refresh,
        }

    async def create_profile(self, user_id: str, data: ProfileCreationSchema):

        data = data.model_dump()

        user_id = uuid.UUID(user_id)

        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        existing_profile = await self.profile_repo.get_user_by_id(user_id)

        if existing_profile is not None:
            raise HTTPException(status_code=422, detail="Profile already created")

        data["user_id"] = user_id
        profile = await self.profile_repo.create(**data)

        await self.profile_repo.session.commit()
        await self.profile_repo.session.refresh(profile)
        return profile

    async def _assemble(self, user):
        existing_profile = await self.profile_repo.get_one(user_id=user.id)
        if existing_profile is None:
            raise HTTPException(status_code=422, detail="Profile not found")

        return UserProfileReadSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            birth_date=existing_profile.birth_date,
            bio=existing_profile.bio,
            country=existing_profile.country,
            phone_number=existing_profile.phone_number,
        )

    async def get_my_profile(self, user_id):
        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        return await self._assemble(user=existing_user)

    async def get_user_profile(self, username):
        existing_user = await self.repo.get_one(username=username)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        return await self._assemble(user=existing_user)
