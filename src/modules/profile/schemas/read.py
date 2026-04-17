from src.modules.profile.schemas.creation import ProfileCreationSchema
from src.modules.auth.schemas.user.read import UserRead


class ProfileReadSchema(ProfileCreationSchema, UserRead):
    pass
