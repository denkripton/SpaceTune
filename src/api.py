from fastapi import FastAPI

from src.utils.interfaces.application import Application
from src.modules import profile_router, music_router, user_router, grade_router
from src import (
    contact,
    description,
    openapi_url,
    summary,
    tags_metadata,
    title,
    version,
)


class API(Application):
    def __init__(self):
        super().__init__()
        self.title = title
        self.summary = summary
        self.description = description
        self.version = version
        self.openapi_url = openapi_url
        self.tags_metadata = tags_metadata
        self.contact = contact
        self.routers = [user_router, music_router, profile_router, grade_router]

    def create(self):
        self.app = FastAPI(
            title=self.title,
            openapi_tags=self.tags_metadata,
            summary=self.summary,
            description=self.description,
            version=self.version,
            openapi_url=self.openapi_url,
            contact=self.contact,
        )
        for router in self.routers:
            self.app.include_router(router=router)


api = API()
api.create()
