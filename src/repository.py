from abc import ABC, abstractmethod


class ABCRepository(ABC):
    @abstractmethod
    async def create():
        pass

    @abstractmethod
    async def get_one():
        pass

    @abstractmethod
    async def delete_obj():
        pass
