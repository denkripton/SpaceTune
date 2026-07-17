from src.aws import bucket_manager as default_bucket_manager
from src.modules.auth.schemas.user.read import UserRead
from src.modules.profile.schemas import (
    ProfilePrivateReadSchema,
    ProfilePublicReadSchema,
)
from src.modules.profile.utils.enums import FieldsVisibility


class ProfileAssembler:
    def __init__(self, bucket_manager=default_bucket_manager):
        self._bucket_manager = bucket_manager

    def _resolve_photo_url(self, profile) -> str | None:
        if profile is None or profile.photo_url is None:
            return None
        return self._bucket_manager.presigned_url(key=profile.photo_url)

    def _is_field_visible(self, profile, field_name: str) -> bool:
        visible = profile.visible_fields or {}
        return visible.get(
            field_name,
            FieldsVisibility.DEFAULT_VISIBLE_FIELDS.value.get(field_name, False),
        )

    def _field_if_visible(self, profile, field_name: str, value):
        return value if self._is_field_visible(profile, field_name) else None

    async def owner(self, user, repo) -> ProfilePrivateReadSchema | UserRead:
        existing_profile = await repo.get_one(user_id=user.id)
        if existing_profile is None:
            return UserRead(id=user.id, username=user.username, email=user.email)

        return ProfilePrivateReadSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            photo_url=self._resolve_photo_url(existing_profile),
            birth_date=existing_profile.birth_date,
            bio=existing_profile.bio,
            country=existing_profile.country,
            phone_number=existing_profile.phone_number,
            visible_fields=existing_profile.visible_fields,
        )

    async def public(self, user, repo) -> ProfilePublicReadSchema | UserRead:
        existing_profile = await repo.get_one(user_id=user.id)
        if existing_profile is None:
            return UserRead(id=user.id, username=user.username, email=user.email)

        return ProfilePublicReadSchema(
            id=user.id,
            username=user.username,
            photo_url=self._resolve_photo_url(existing_profile),
            email=self._field_if_visible(existing_profile, "email", user.email),
            birth_date=self._field_if_visible(
                existing_profile, "birth_date", existing_profile.birth_date
            ),
            bio=self._field_if_visible(existing_profile, "bio", existing_profile.bio),
            country=self._field_if_visible(
                existing_profile, "country", existing_profile.country
            ),
            phone_number=self._field_if_visible(
                existing_profile, "phone_number", existing_profile.phone_number
            ),
        )


profile_assembler = ProfileAssembler()
