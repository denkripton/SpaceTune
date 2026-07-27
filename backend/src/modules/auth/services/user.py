from src.modules.auth.repository import UserRepository
from src.modules.auth.schemas.password import PasswordChangeSchema, PasswordCreateSchema
from src.modules.auth.schemas.user.creation import UserCreateSchema
from src.modules.auth.schemas.user.login import UserLoginSchema
from src.modules.auth.utils import JWT, pw_manager
from src.modules.auth.utils.enums import PasswordHash
from src.utils import UnitOfWork
from src.utils.exceptions import ServiceError


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        jwt: JWT,
        uow: UnitOfWork,
    ):
        self.__repo = repo
        self.__jwt = jwt
        self.__uow = uow

    async def register(self, data: UserCreateSchema):
        data = data.model_dump()

        existing_user = await self.__repo.get_by_email(data["email"])

        if existing_user is not None:
            raise ServiceError(code=422, msg="User already exists")

        existing_username = await self.__repo.get_one(username=data["username"])

        if existing_username is not None:
            raise ServiceError(code=422, msg="That username already taken")

        data["password"] = pw_manager.hash_password(data["password"])

        user = await self.__repo.create(**data)

        await self.__uow.commit(conflict_msg="User already exists")
        await self.__uow.refresh(user)
        return user

    async def login(self, data: UserLoginSchema):
        existing_user = await self.__repo.get_by_email(data.email)

        valid_hash = (
            existing_user.password
            if existing_user is not None and existing_user.password is not None
            else PasswordHash.DUMMY_PASSWORD_HASH.value
        )
        password_check = pw_manager.check_password(data.password, valid_hash)

        if (
            existing_user is None
            or existing_user.password is None
            or not password_check
        ):
            raise ServiceError(code=403, msg="Invalid email or password")

        user_id = str(existing_user.id)
        access = self.__jwt.create_access_token(user_id)
        refresh = self.__jwt.create_refresh_token(user_id)

        return {
            "access": access,
            "refresh": refresh,
        }

    async def set_password(self, user_id, data: PasswordCreateSchema):
        existing_user = await self.__repo.get_by_id_locked(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        if existing_user.password is not None:
            raise ServiceError(code=409, msg="User password already exists")

        data = data.model_dump()

        existing_user.password = pw_manager.hash_password(data["password"])

        await self.__uow.commit()
        await self.__uow.refresh(existing_user)

        return "Password added successfully"

    async def change_password(self, user_id, data: PasswordChangeSchema):
        existing_user = await self.__repo.get_by_id_locked(id=user_id)

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

        await self.__uow.commit()
        await self.__uow.refresh(existing_user)

        return "Password changed successfully"
