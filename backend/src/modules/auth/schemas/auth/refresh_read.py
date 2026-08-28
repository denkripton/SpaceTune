from src.utils.schemas.base_schema import BaseSchema


class TokenRefreshReadSchema(BaseSchema):
    access: str
