from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.users import User as UserModel
from src.models.users import UserRole


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, user_id: int) -> UserModel | None:
        return await self.db.get(UserModel, user_id)

    async def get_by_username(self, username: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(self, limit: int, offset: int) -> list[UserModel]:
        stmt = select(UserModel).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add(self, user: UserModel) -> UserModel:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: UserModel) -> UserModel:
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: UserModel) -> None:
        await self.db.delete(user)
        await self.db.flush()

    async def count_admins(self) -> int:
        stmt = select(func.count(UserModel.id)).where(UserModel.role == UserRole.admin)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id_with_orders(self, user_id: int) -> UserModel | None:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.orders))
            .where(UserModel.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
