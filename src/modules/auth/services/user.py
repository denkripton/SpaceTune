import uuid

from src.exceptions import ServiceError

from src.modules.auth.schemas.user.login import UserLoginSchema
from src.modules.auth.schemas.user.creation import UserCreateSchema

from src.modules.profile.repository import ProfileRepository
from src.modules.auth.repository import UserRepository
from src.modules.auth.utils import JWT, pw_manager

from src.modules.profile.utils import assemble


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
            raise ServiceError(code=422, msg="User already exists")

        data["password"] = pw_manager.hash_password(data["password"])

        user = await self.repo.create(**data)

        await self.repo.session.commit()
        await self.repo.session.refresh(user)
        return user

    async def login(self, data: UserLoginSchema):
        existing_user = await self.repo.get_by_email(data.email)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        password_check = pw_manager.check_password(
            data.password, existing_user.password
        )
        existing_user.id = str(existing_user.id)

        if password_check is False:
            raise ServiceError(code=403, msg="Incorrect password")

        access = self.jwt.create_access_token(existing_user.id)
        refresh = self.jwt.create_refresh_token(existing_user.id)

        return {
            "access": access,
            "refresh": refresh,
        }

    async def update_username(self, user_id, new_username):
        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")


        existing_user.username = new_username

        await self.repo.session.commit()
        await self.repo.session.refresh(existing_user)
        return await assemble(user=existing_user, repo=self.profile_repo)
