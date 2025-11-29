from fastapi import Depends

from src.data_base.dependencies import Db_session
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.services.orders.service import OrderService


def get_order_repository(db: Db_session) -> OrderRepository:
    return OrderRepository(db)


def get_product_repository(db: Db_session) -> ProductRepository:
    return ProductRepository(db)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
) -> OrderService:
    return OrderService(order_repo, product_repo)
