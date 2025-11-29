from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.products import Product as ProductModel


class ProductRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, product_id: int) -> ProductModel | None:
        return await self.db.get(ProductModel, product_id)

    async def get_by_name(self, product_name: str) -> ProductModel | None:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.name == product_name)
        )
        return result.scalars().first()

    async def get_all(self, limit: int, offset: int) -> list[ProductModel]:
        results = await self.db.execute(
            select(ProductModel).limit(limit).offset(offset)
        )
        return list(results.scalars().all())

    async def add(self, product: ProductModel) -> ProductModel:
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product: ProductModel) -> ProductModel:
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete(self, product: ProductModel) -> None:
        await self.db.delete(product)
        await self.db.flush()

    async def get_by_id_for_delete_validation(
        self, product_id: int
    ) -> ProductModel | None:
        stmt = (
            select(ProductModel)
            .options(selectinload(ProductModel.order_items))
            .where(ProductModel.id == product_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_many_by_ids_with_lock(
        self, product_ids: list[int]
    ) -> list[ProductModel]:
        stmt = (
            select(ProductModel)
            .where(ProductModel.id.in_(product_ids))
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
