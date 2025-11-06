from fastapi import APIRouter, Depends, HTTPException, status

from src.schemas.orders import OrderCreate, ReadOrder
from src.auth.dependencies import Current_user
from src.services.orders.service import OrderService
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.data_base.dependencies import Db_session

def get_order_repository(db: Db_session) -> OrderRepository:
    return OrderRepository(db)

def get_product_repository(db: Db_session) -> ProductRepository:
    return ProductRepository(db)

def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository)
) -> OrderService:
    return OrderService(order_repo, product_repo)


router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=ReadOrder, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    order_data: OrderCreate,
    current_user: Current_user,
    service: OrderService = Depends(get_order_service)
):
    new_order = await service.create_order(order_data, current_user)
    return new_order

@router.get("/{order_id}", response_model=ReadOrder)
async def read_order(
    order_id: int,
    current_user: Current_user,
    service: OrderService = Depends(get_order_service)
):
    order = await service.get_order_by_id_for_user(order_id, current_user.id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return order

@router.get("/", response_model=list[ReadOrder])
async def read_all_my_orders(
    current_user: Current_user,
    limit: int = 20,
    offset: int = 0,
    service: OrderService = Depends(get_order_service)
):
    orders = await service.get_all_orders_for_user(current_user.id, limit, offset)
    return orders