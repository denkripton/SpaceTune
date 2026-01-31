from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UsersCreationSchema, ProfileCreationSchema
from src.auth.models import User, UserProfile
from src.auth.utils.hash_generation import Password


pasword_hash = Password()


async def create_user(creds: UsersCreationSchema, session: AsyncSession):
    hashed_password = pasword_hash.hash_password(creds.password)

    user_to_db = User(
        username=creds.username, email=creds.email, password=hashed_password
    )

    session.add(user_to_db)
    await session.commit()
    await session.refresh(user_to_db)

    return user_to_db


async def create_profile(user:str, profile: ProfileCreationSchema, session: AsyncSession):
    profile_to_db = UserProfile(birth_date=profile.birth_date, bio=profile.bio, user_username=user)

    session.add(profile_to_db)
    await session.commit()
    await session.refresh(profile_to_db)

    return profile_to_db