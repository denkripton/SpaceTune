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

    def _resolve_photo_url(self, user) -> str | None:
        if user is None or user.photo_url is None:
            return None
        return self._bucket_manager.presigned_url(key=user.photo_url)

    def _is_field_visible(self, profile, field_name: str) -> bool:
        visible = profile.visible_fields or {}
        return visible.get(
            field_name,
            FieldsVisibility.DEFAULT_VISIBLE_FIELDS.value.get(field_name, False),
        )

    def _field_if_visible(self, profile, field_name: str, value):
        return value if self._is_field_visible(profile, field_name) else None

    def _sanitized_visible_fields(self, profile) -> dict[str, bool]:
        raw = profile.visible_fields or {}
        return {
            field: bool(raw[field])
            for field in FieldsVisibility.VISIBILITY_TOGGLEABLE_FIELDS.value
            if field in raw
        }

    async def owner(self, user, repo) -> ProfilePrivateReadSchema | UserRead:
        existing_profile = await repo.get_one(user_id=user.id)
        if existing_profile is None:
            return ProfilePrivateReadSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                photo_url=self._resolve_photo_url(user),
                birth_date=None,
                bio=None,
                country=None,
                phone_number=None,
                visible_fields=dict(FieldsVisibility.DEFAULT_VISIBLE_FIELDS.value),
            )

        return ProfilePrivateReadSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            photo_url=self._resolve_photo_url(user),
            birth_date=existing_profile.birth_date,
            bio=existing_profile.bio,
            country=existing_profile.country,
            phone_number=existing_profile.phone_number,
            visible_fields=self._sanitized_visible_fields(existing_profile),
        )

    async def public(self, user, repo) -> ProfilePublicReadSchema:
        existing_profile = await repo.get_one(user_id=user.id)
        if existing_profile is None:
            return ProfilePublicReadSchema(
                id=user.id,
                username=user.username,
                photo_url=self._resolve_photo_url(user),
            )

        return ProfilePublicReadSchema(
            id=user.id,
            username=user.username,
            photo_url=self._resolve_photo_url(user),
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
