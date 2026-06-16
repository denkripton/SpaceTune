from src.exceptions import ServiceError
from src.modules.auth.repository import UserRepository
from src.modules.auth.schemas.password import PasswordChangeSchema, PasswordCreateSchema
from src.modules.auth.schemas.user.creation import UserCreateSchema
from src.modules.auth.schemas.user.login import UserLoginSchema
from src.modules.auth.utils import JWT, pw_manager
from src.modules.profile.repository import ProfileRepository
from src.modules.profile.utils import assemble


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        profile_repo: ProfileRepository,
        jwt: JWT,
    ):
        self.__profile_repo = profile_repo
        self.__repo = repo
        self.__jwt = jwt

    async def register(self, data: UserCreateSchema):
        data = data.model_dump()

        existing_user = await self.__repo.get_by_email(data["email"])

        if existing_user is not None:
            raise ServiceError(code=422, msg="User already exists")

        data["password"] = pw_manager.hash_password(data["password"])

        user = await self.__repo.create(**data)

        await self.__repo.session.commit()
        await self.__repo.session.refresh(user)
        return user

    async def login(self, data: UserLoginSchema):
        existing_user = await self.__repo.get_by_email(data.email)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        password_check = pw_manager.check_password(
            data.password, existing_user.password
        )
        existing_user.id = str(existing_user.id)

        if password_check is False:
            raise ServiceError(code=403, msg="Incorrect password")

        access = self.__jwt.create_access_token(existing_user.id)
        refresh = self.__jwt.create_refresh_token(existing_user.id)

        return {
            "access": access,
            "refresh": refresh,
        }

    async def set_password(self, user_id, data: PasswordCreateSchema):
        existing_user = await self.__repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        if existing_user.password is not None:
            raise ServiceError(code=409, msg="User password already exists")

        data = data.model_dump()

        existing_user.password = pw_manager.hash_password(data["password"])

        await self.__repo.session.commit()
        await self.__repo.session.refresh(existing_user)

        return "Password added successfully"

    async def change_password(self, user_id, data: PasswordChangeSchema):
        existing_user = await self.__repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        if existing_user.password is None:
            raise ServiceError(code=400, msg="Password is not set")

        data = data.model_dump()

        password_check = pw_manager.check_password(
            input_password=data["password"], valid_password=existing_user.password
        )

        if password_check is False:
            raise ServiceError(code=403, msg="Incorrect password")

        existing_user.password = pw_manager.hash_password(data["new_password"])

        await self.__repo.session.commit()
        await self.__repo.session.refresh(existing_user)

        return "Password changed successfully"


