from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.orders import Order as OrderModel


class OrderRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def add(self, order: OrderModel) -> OrderModel:
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order, attribute_names=["items"])
        return order

    async def get_by_id_and_user(
        self, order_id: int, user_id: int
    ) -> OrderModel | None:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.order_id == order_id, OrderModel.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_for_user(
        self, user_id: int, limit: int, offset: int
    ) -> list[OrderModel]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.order_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
