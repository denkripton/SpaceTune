from abc import ABC, abstractmethod
from src.auth.schemas import UserCreateSchema, UserRead, UserLoginSchema


class UserRepository(ABC):
    @abstractmethod
    async def create(self, data: UserCreateSchema) -> UserRead:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserRead | None:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> UserRead | None:
        pass
