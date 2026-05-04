import uuid

from src.exceptions import ServiceError

from src.modules.profile.schemas.creation import ProfileCreationSchema

from src.modules.profile.utils import assemble
from src.modules.profile.repository import ProfileRepository
from src.modules.auth.repository import UserRepository

from src.modules.auth.utils import pw_manager


class ProfileService:
    def __init__(
        self,
        repo: UserRepository,
        profile_repo: ProfileRepository,
    ):
        self.profile_repo = profile_repo
        self.repo = repo

    async def create_profile(self, user_id: str, data: ProfileCreationSchema):

        data = data.model_dump()

        user_id = uuid.UUID(user_id)

        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        existing_profile = await self.profile_repo.get_user_by_id(user_id)

        if existing_profile is not None:
            raise ServiceError(code=422, msg="Profile already created")

        data["user_id"] = user_id
        profile = await self.profile_repo.create(**data)

        await self.profile_repo.session.commit()
        await self.profile_repo.session.refresh(profile)
        return profile

    async def get_my_profile(self, user_id):
        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        return await assemble(user=existing_user, repo=self.profile_repo)

    async def get_user_profile(self, username):
        existing_user = await self.repo.get_one(username=username)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        return await assemble(user=existing_user, repo=self.profile_repo)

    async def delete_profile(self, user_id):
        existing_user = await self.repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        existing_profile = await self.profile_repo.get_one(user_id=existing_user.id)

        if existing_profile is None:
            raise ServiceError(code=422, msg="Profile does not exist")

        await self.profile_repo.delete_obj(existing_profile.id)
        await self.profile_repo.session.commit()
        return "Profile has been deleted succesfuly"
