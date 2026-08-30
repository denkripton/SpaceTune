import uuid

from src.aws import bucket_manager
from src.modules.auth.repository import UserRepository
from src.modules.profile.repository import ProfileRepository
from src.modules.profile.schemas.creation import ProfileCreationSchema
from src.modules.profile.schemas.update import ProfileUpdateSchema
from src.modules.profile.schemas.visibility import ProfileVisibilityUpdateSchema
from src.modules.profile.utils import profile_assembler
from src.modules.profile.utils.enums import PFPSizeLimit, ProfileMediaTypes
from src.utils import UnitOfWork
from src.utils.exceptions import (
    ConflictError,
    FileSizeLimitExceeded,
    NotFoundError,
    ValidationError,
)
from src.utils.uploads import SizeLimitedStream


class ProfileService:
    def __init__(
        self,
        repo: UserRepository,
        profile_repo: ProfileRepository,
        uow: UnitOfWork,
    ):
        self.__profile_repo = profile_repo
        self.__user_repo = repo
        self.__uow = uow

    async def create_profile(self, user, data: ProfileCreationSchema):

        data = data.model_dump()

        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        existing_profile = await self.__profile_repo.get_user_by_id(user.id)

        if existing_profile is not None:
            raise ConflictError(msg="Profile already created")

        data["user_id"] = user.id
        profile = await self.__profile_repo.create(**data)

        await self.__uow.commit(conflict_msg="Profile already created")
        await self.__uow.refresh(profile)
        return profile

    async def get_my_profile(self, user):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )

    async def get_user_profile(self, user_id: uuid.UUID):
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        return await profile_assembler.public(
            user=existing_user, repo=self.__profile_repo
        )

    async def delete_profile(self, user):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        existing_profile = await self.__profile_repo.get_one(user_id=existing_user.id)

        if existing_profile is None:
            raise NotFoundError(msg="Profile does not exist")

        await self.__profile_repo.delete_obj(existing_profile.id)
        await self.__uow.commit()

        return "Profile has been deleted succesfuly"

    async def update_username(self, user, new_username):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        existing_username = await self.__user_repo.get_one(username=new_username)

        if existing_username is not None:
            raise ConflictError(msg="That username already taken")

        existing_user.username = new_username

        await self.__uow.commit(conflict_msg="That username already taken")
        await self.__uow.refresh(existing_user)
        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )

    async def update_profile(self, user, data: ProfileUpdateSchema):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        existing_profile = await self.__profile_repo.get_one(user_id=existing_user.id)

        if existing_profile is None:
            raise NotFoundError(msg="Profile does not exist")

        for field_name in data.model_fields_set:
            setattr(existing_profile, field_name, getattr(data, field_name))

        await self.__uow.commit()
        await self.__uow.refresh(existing_profile)
        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )

    async def update_visibility(self, user, data: ProfileVisibilityUpdateSchema):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        existing_profile = await self.__profile_repo.get_one(user_id=existing_user.id)

        if existing_profile is None:
            raise NotFoundError(msg="Profile does not exist")
        updates = data.model_dump(exclude_unset=True)
        existing_profile.visible_fields.update(updates)

        await self.__uow.commit()
        await self.__uow.refresh(existing_profile)
        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )

    async def upload_photo(self, user, photo_file):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        if photo_file.content_type not in ProfileMediaTypes.PHOTO_TYPES.value:
            raise ValidationError(msg="Invalid image file type")

        if (
            photo_file.size is not None
            and photo_file.size > PFPSizeLimit.MAX_PHOTO_SIZE
        ):
            raise ValidationError(msg="Photo file is too big")

        old_photo_key = existing_user.photo_url
        new_photo_key = f"profile/{existing_user.id}/{uuid.uuid4()}"

        try:
            limited_stream = SizeLimitedStream(
                photo_file.file, max_bytes=PFPSizeLimit.MAX_PHOTO_SIZE
            )
            await bucket_manager.upload_file(
                file=limited_stream,
                file_type=photo_file.content_type,
                key=new_photo_key,
            )
        except FileSizeLimitExceeded:
            raise

        existing_user.photo_url = new_photo_key
        await self.__uow.commit()
        await self.__uow.refresh(existing_user)

        if old_photo_key is not None:
            try:
                await bucket_manager.delete_file(key=old_photo_key)
            except Exception:
                pass

        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )

    async def delete_photo(self, user):
        existing_user = await self.__user_repo.get_by_id(id=user.id)

        if existing_user is None:
            raise NotFoundError(msg="User does not exist")

        if existing_user.photo_url is None:
            raise NotFoundError(msg="No photo set for this user")

        old_photo_key = existing_user.photo_url
        existing_user.photo_url = None
        await self.__uow.commit()
        await self.__uow.refresh(existing_user)

        try:
            await bucket_manager.delete_file(key=old_photo_key)
        except Exception:
            pass

        return await profile_assembler.owner(
            user=existing_user, repo=self.__profile_repo
        )
