import os
from dotenv import load_dotenv

load_dotenv()

pg_user = os.getenv("PGUSER")
pg_password = os.getenv("PGPASSWORD")
db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{pg_user}:{pg_password}@{db_host}:{db_port}/{db_name}"
)