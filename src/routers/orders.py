from fastapi import APIRouter, HTTPException, status

from src.data_base.dependencies import Db_session
from src.schemas.orders import OrderCreate, ReadOrder
from src.services.orders.service import create_order, get_order_by_id_for_user, get_all_orders_for_user
from src.auth.dependencies import Current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=ReadOrder, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    order_data: OrderCreate,
    db: Db_session,
    current_user: Current_user
):
    """
    Create a new order for the authenticated user.

    Args:
        order_data (OrderCreate): The order details, including a list of items.
        db (Db_session): Database session dependency.
        current_user (Current_user): The authenticated user placing the order.

    Returns:
        ReadOrder: The newly created order data.

    Raises:
        HTTPException:
            - 400 (Bad Request): If the order contains no items.
            - 404 (Not Found): If a product in the order does not exist.
            - 409 (Conflict): If there is insufficient stock or a product is unavailable.
    """
    new_order = await create_order(db, order_data, current_user)
    
    return new_order

@router.get("/{order_id}", response_model=ReadOrder)
async def read_order(
    order_id: int,
    db: Db_session,
    current_user: Current_user
):
    """
    Retrieve a specific order by its ID.

    Args:
        order_id (int): The ID of the order to retrieve.
        db (Db_session): Database session dependency.
        current_user (Current_user): The authenticated user making the request.

    Returns:
        ReadOrder: The order data if found and it belongs to the user.

    Raises:
        HTTPException: 404 (Not Found) if the order does not exist or does not
                       belong to the current user.
    """
    order = await get_order_by_id_for_user(db, order_id, current_user.id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return order

@router.get("/", response_model=list[ReadOrder])
async def read_all_my_orders(
    db: Db_session,
    current_user: Current_user,
    limit: int = 20,
    offset: int = 0
):
    """
    Retrieve the order history for the currently authenticated user.

    Args:
        db (Db_session): Database session dependency.
        current_user (Current_user): The authenticated user.
        limit (int): Maximum number of orders to return.
        offset (int): Number of orders to skip for pagination.

    Returns:
        list[ReadOrder]: A list of the user's orders.
    """
    orders = await get_all_orders_for_user(db, current_user.id, limit, offset)
    return orders