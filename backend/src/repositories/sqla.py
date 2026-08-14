import uuid
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.interfaces.repository import ABCRepository


class SQLAlchemyRepository(ABCRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    @override
    async def get_one(self, **kwargs):
        conditions = []

        for key, value in kwargs.items():
            if value is not None:
                conditions.append(getattr(self.model, key) == value)

        query = select(self.model).where(*conditions)
        data = await self.session.execute(query)
        obj = data.scalars().first()
        return obj

    async def get_by_id_locked(self, id: uuid.UUID):
        query = select(self.model).where(self.model.id == id).with_for_update()
        data = await self.session.execute(query)
        return data.scalars().first()
    
    @override
    async def get_many(self, skip: int = 0, limit: int = None, **kwargs):
        conditions = []

        for key, value in kwargs.items():
            if value is not None:
                conditions.append(getattr(self.model, key) == value)

        query = select(self.model).where(*conditions).offset(skip).limit(limit)
        data = await self.session.execute(query)
        objs = data.scalars().all()
        return objs

    async def get_by_id(self, id: uuid.UUID):
        return await self.get_one(id=id)

    @override
    async def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.session.add(obj)
        return obj

    @override
    async def delete_obj(self, id: uuid.UUID):
        obj = await self.get_one(id=id)
        await self.session.delete(obj)
        return obj
