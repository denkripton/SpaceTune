from fastapi import FastAPI
import uvicorn
from src.modules.auth.router import user_router
from src.modules.music.router import music_router

app = FastAPI()

app.include_router(user_router)
app.include_router(music_router)



if __name__ == "__main__":
    uvicorn.run(app)
