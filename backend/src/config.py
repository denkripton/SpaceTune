import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    DB_URL: str

    JWT_SECRET_KEY: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_USERINFO_URL: str

    AWS_SECRET: str
    AWS_ACCESS: str
    AWS_REGION: str

    BUCKET_NAME: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
logger = logging.getLogger(__name__)
