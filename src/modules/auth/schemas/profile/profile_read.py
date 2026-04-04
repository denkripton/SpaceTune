from src.modules.auth.schemas.profile.profile_creation import ProfileCreationSchema
from src.modules.auth.schemas.user.read import UserRead


class UserProfileReadSchema(ProfileCreationSchema, UserRead):
    pass
