import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    TEST_DB_PORT: int = 5433

    JWT_SECRET_KEY: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_USERINFO_URL: str

    AWS_SECRET: str
    AWS_ACCESS: str
    AWS_REGION: str

    BUCKET_NAME: str

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @property
    def DB_URL(self) -> str:
        return self._engine_url(self.DB_PORT, self.DB_NAME)

    @property
    def TEST_DB_URL(self) -> str:
        return self._engine_url(self.TEST_DB_PORT, f"{self.DB_NAME}_test")

    def _engine_url(self, port: int, database: str) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{port}/{database}"
        )


settings = Settings()
logger = logging.getLogger(__name__)
