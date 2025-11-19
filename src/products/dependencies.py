from fastapi import Depends
from src.data_base.dependencies import Db_session
from src.cache.dependencies import Redis_session
from src.repositories.product_repository import ProductRepository
from src.services.products.service import ProductService

def get_product_repository(db: Db_session) -> ProductRepository:
    return ProductRepository(db)

def get_product_service(
    redis: Redis_session,
    repo: ProductRepository = Depends(get_product_repository)
) -> ProductService:
    return ProductService(repo, redis)