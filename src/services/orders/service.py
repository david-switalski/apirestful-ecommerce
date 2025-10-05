from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.orders import Order as OrderModel, OrderItem
from src.models.products import Product as ProductModel
from src.models.users import User as UserModel
from src.schemas.orders import OrderCreate
from src.core.exceptions import ProductNotFound, InsufficientStock, EmptyOrder, ProductUnavailableError

async def create_order(db: AsyncSession, order_data: OrderCreate, current_user: UserModel) -> OrderModel:
    if not order_data.items:
        raise EmptyOrder()

    product_ids = [item.product_id for item in order_data.items]
    
    stmt = (
        select(ProductModel)
        .where(ProductModel.id.in_(product_ids))
        .with_for_update()
    )
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    product_map = {p.id: p for p in products}

    for item in order_data.items:
        product = product_map.get(item.product_id)
        if not product:
            raise ProductNotFound(item.product_id)
        
        if product.stock < item.quantity:
            raise InsufficientStock(
                product_id=product.id,
                product_name=product.name,
                requested=item.quantity,
                available=product.stock
            )
        
        if not product.available:
            raise ProductUnavailableError(
                product_name=product.name
            )

    total_price = Decimal("0.0")
    order_items = []
    for item in order_data.items:
        product = product_map[item.product_id]
        
        order_item = OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price
        )
        order_items.append(order_item)
        
        total_price += product.price * item.quantity
        
        product.stock -= item.quantity

    new_order = OrderModel(
        user_id=current_user.id,
        total_price=total_price,
        items=order_items  
    )

    db.add(new_order)
    await db.flush()
    await db.refresh(new_order, attribute_names=['items']) 
    
    return new_order

async def get_order_by_id_for_user(db: AsyncSession, order_id: int, user_id: int) -> OrderModel | None:
    stmt = (
        select(OrderModel)
        .options(selectinload(OrderModel.items)) 
        .where(OrderModel.order_id == order_id)
        .where(OrderModel.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_all_orders_for_user(db: AsyncSession, user_id: int, limit: int, offset: int) -> list[OrderModel]:
    stmt = (
        select(OrderModel)
        .options(selectinload(OrderModel.items)) 
        .where(OrderModel.user_id == user_id)
        .order_by(OrderModel.order_date.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()