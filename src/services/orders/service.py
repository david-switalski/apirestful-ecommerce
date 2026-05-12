from decimal import Decimal

import structlog
from redis.asyncio import Redis

from src.cache.scripts import DEDUCT_STOCK_SCRIPT, ROLLBACK_STOCK_SCRIPT
from src.core.exceptions import (
    EmptyOrderError,
    InsufficientStockError,
    ProductNotFoundError,
    ProductUnavailableError,
)
from src.models.orders import Order as OrderModel
from src.models.orders import OrderItem
from src.models.users import User as UserModel
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.schemas.orders import OrderCreate, ReadOrder

logger = structlog.get_logger()


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        redis_client: Redis,
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.redis = redis_client

        self.deduct_script = self.redis.register_script(DEDUCT_STOCK_SCRIPT)
        self.rollback_script = self.redis.register_script(ROLLBACK_STOCK_SCRIPT)

    async def create_order(
        self, order_data: OrderCreate, current_user: UserModel
    ) -> ReadOrder:
        if not order_data.items:
            raise EmptyOrderError()

        product_ids = [item.product_id for item in order_data.items]

        products = await self.product_repo.get_many_by_ids(product_ids)
        product_map = {p.id: p for p in products}

        keys = []
        args = []
        total_price = Decimal("0.0")
        order_items = []

        for item in order_data.items:
            product = product_map.get(item.product_id)
            if not product:
                raise ProductNotFoundError(item.product_id)
            if not product.available:
                raise ProductUnavailableError(product_name=product.name)

            keys.append(f"inventory:{product.id}")
            args.append(item.quantity)

            price_decimal = Decimal(str(product.price))
            total_price += price_decimal * item.quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=price_decimal,
                )  # type: ignore[call-arg]
            )

        result = await self.deduct_script(keys=keys, args=args)

        if result[0] == -1:
            missing_key = result[1]
            missing_id = int(missing_key.split(":")[1])
            logger.warning("cache_miss_inventory", product_id=missing_id)

            missing_product = product_map[missing_id]
            await self.redis.set(missing_key, missing_product.stock)

            result = await self.deduct_script(keys=keys, args=args)

        if result[0] == -2:
            failed_key = result[1]
            failed_id = int(failed_key.split(":")[1])
            current_stock = result[2]
            failed_product = product_map[failed_id]

            requested_qty = next(
                item.quantity
                for item in order_data.items
                if item.product_id == failed_id
            )

            raise InsufficientStockError(
                product_id=failed_id,
                product_name=failed_product.name,
                requested=requested_qty,
                available=current_stock,
            )

        new_order_model = OrderModel(
            user_id=current_user.id, total_price=total_price, items=order_items
        )  # type: ignore[call-arg]

        try:
            created_order = await self.order_repo.add(new_order_model)

            for item in order_data.items:
                product = product_map[item.product_id]
                product.stock -= item.quantity
            await self.product_repo.db.flush()

            logger.info(
                "order_created_successfully",
                order_id=created_order.order_id,
                user_id=current_user.id,
            )
            return ReadOrder.model_validate(created_order)

        except Exception as e:
            logger.error(
                "db_insert_failed_rolling_back_redis",
                error=str(e),
                user_id=current_user.id,
            )
            await self.rollback_script(keys=keys, args=args)
            raise e

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
