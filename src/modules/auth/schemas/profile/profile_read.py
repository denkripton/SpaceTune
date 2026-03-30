from src.modules.auth.schemas.profile.profile_creation import ProfileCreationSchema
from src.modules.auth.schemas.user.user_read import UserRead


class UserProfileReadSchema(ProfileCreationSchema, UserRead):
    pass
