from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from src.databases.sql_db import create_tables, SQLALCHEMY_DATABASE_URL, engine
from src.auth import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await engine.dispose

app = FastAPI(lifespan=lifespan)

app.include_router(router.router)


if __name__ == "__main__":
    uvicorn.run(app)
