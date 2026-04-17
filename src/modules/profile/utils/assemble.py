from src.modules.profile.schemas.read import ProfileReadSchema

from src.modules.auth.schemas.user.read import UserRead


async def assemble(user, repo):
    existing_profile = await repo.get_one(user_id=user.id)
    if existing_profile is None:
        return UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
        )

    return ProfileReadSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        birth_date=existing_profile.birth_date,
        bio=existing_profile.bio,
        country=existing_profile.country,
        phone_number=existing_profile.phone_number,
    )