from fastapi import FastAPI
import uvicorn
from src.auth import router


app = FastAPI()

app.include_router(router.router)


if __name__ == "__main__":
    uvicorn.run(app)
