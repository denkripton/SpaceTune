from src.auth.schemas import UserCreate
from src.auth.repository import UserRepository


class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserCreate):
        return await self.repo.create(data)
