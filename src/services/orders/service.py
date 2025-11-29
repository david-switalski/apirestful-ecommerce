from decimal import Decimal

from src.core.exceptions import EmptyOrder
from src.core.exceptions import InsufficientStock
from src.core.exceptions import ProductNotFound
from src.core.exceptions import ProductUnavailableError
from src.models.orders import Order as OrderModel
from src.models.orders import OrderItem
from src.models.users import User as UserModel
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.schemas.orders import OrderCreate
from src.schemas.orders import ReadOrder


class OrderService:
    def __init__(self, order_repo: OrderRepository, product_repo: ProductRepository):
        self.order_repo = order_repo
        self.product_repo = product_repo

    async def create_order(
        self, order_data: OrderCreate, current_user: UserModel
    ) -> ReadOrder:
        if not order_data.items:
            raise EmptyOrder()

        product_ids = [item.product_id for item in order_data.items]

        products = await self.product_repo.get_many_by_ids_with_lock(product_ids)
        product_map = {p.id: p for p in products}

        for item in order_data.items:
            product = product_map.get(item.product_id)
            if not product:
                raise ProductNotFound(item.product_id)

            if product.stock is None:
                raise ValueError(f"Product {product.id} has invalid stock data")

            if product.name is None:
                raise ValueError(f"Product {product.id} has no name")

            if product.stock < item.quantity:
                raise InsufficientStock(
                    product_id=product.id,
                    product_name=product.name,
                    requested=item.quantity,
                    available=product.stock,
                )

            if not product.available:
                raise ProductUnavailableError(product_name=product.name)

        total_price = Decimal("0.0")
        order_items = []
        for item in order_data.items:
            product = product_map[item.product_id]

            price_decimal = Decimal(str(product.price))

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=price_decimal,
                )  # type: ignore
            )

            total_price += price_decimal * item.quantity

            if product is not None and product.stock is not None:
                product.stock -= item.quantity

        new_order_model = OrderModel(
            user_id=current_user.id, total_price=total_price, items=order_items
        )  # type: ignore

        created_order = await self.order_repo.add(new_order_model)

        return ReadOrder.model_validate(created_order)

    async def get_order_by_id_for_user(
        self, order_id: int, user_id: int
    ) -> ReadOrder | None:
        order_model = await self.order_repo.get_by_id_and_user(order_id, user_id)
        if order_model:
            return ReadOrder.model_validate(order_model)
        return None

    async def get_all_orders_for_user(
        self, user_id: int, limit: int, offset: int
    ) -> list[ReadOrder]:
        order_models = await self.order_repo.get_all_for_user(user_id, limit, offset)
        return [ReadOrder.model_validate(order) for order in order_models]
