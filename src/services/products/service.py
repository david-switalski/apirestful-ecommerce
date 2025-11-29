from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from redis.asyncio import Redis
from src.core.exceptions import ProductInUseError
from src.core.exceptions import ProductNameAlreadyExistsError
from src.models.products import Product as ProductModel
from src.repositories.product_repository import ProductRepository
from src.schemas.products import CreateProduct
from src.schemas.products import ReadAllProducts
from src.schemas.products import ReadProduct
from src.schemas.products import UpdateProduct


class ProductService:
    def __init__(self, repository: ProductRepository, redis_client: Redis):
        self.repo = repository
        self.redis = redis_client

    async def get_product_by_id(self, product_id: int) -> ReadProduct | None:
        cache_key = f"product:{product_id}"

        if cached_product := await self.redis.get(cache_key):
            return ReadProduct.model_validate_json(cached_product)

        product_model = await self.repo.get_by_id(product_id)

        if product_model:
            product_schema = ReadProduct.model_validate(product_model)
            await self.redis.set(
                name=cache_key, value=product_schema.model_dump_json(), ex=600
            )

            return product_schema

        return None

    async def get_all_products(self, limit: int, offset: int) -> list[ReadAllProducts]:
        product_models = await self.repo.get_all(limit=limit, offset=offset)

        return [ReadAllProducts.model_validate(p) for p in product_models]

    async def create_product(self, product_data: CreateProduct) -> ReadProduct:
        if await self.repo.get_by_name(product_data.name):
            raise ProductNameAlreadyExistsError(name=product_data.name)

        product_model = ProductModel(**product_data.model_dump())

        try:
            created_model = await self.repo.add(product_model)
        except IntegrityError as exc:
            if isinstance(exc.orig, UniqueViolationError):
                raise ProductNameAlreadyExistsError(name=product_data.name)
            else:
                raise

        return ReadProduct.model_validate(created_model)

    async def update_product(
        self, product_id: int, product_update_data: UpdateProduct
    ) -> ReadProduct | None:
        product_model = await self.repo.get_by_id(product_id)
        if not product_model:
            return None

        update_data = product_update_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product_model, key, value)

        updated_model = await self.repo.update(product_model)

        await self.redis.delete(f"product:{product_id}")

        return ReadProduct.model_validate(updated_model)

    async def delete_product(self, product_id: int) -> bool:
        product_model = await self.repo.get_by_id_for_delete_validation(product_id)
        if not product_model:
            return False

        if product_model.order_items:
            raise ProductInUseError(product_name=product_model.name)

        await self.repo.delete(product_model)

        await self.redis.delete(f"product:{product_id}")

        return True
