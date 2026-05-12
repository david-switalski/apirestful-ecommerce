import json
import secrets
import time
from datetime import UTC, datetime
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
from src.models.orders import OrderState
from src.models.users import User as UserModel
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.schemas.orders import OrderCreate, ReadOrder, ReadOrderItem

logger = structlog.get_logger()


def generate_order_id() -> int:
    timestamp_ms = int(time.time() * 1000)
    return (timestamp_ms << 22) | (1 << 12) | secrets.randbelow(4096)


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

        order_id = generate_order_id()

        items_payload = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": str(product_map[item.product_id].price),
            }
            for item in order_data.items
        ]

        event_data = {
            "order_id": str(order_id),
            "user_id": str(current_user.id),
            "total_price": str(total_price),
            "items": json.dumps(items_payload),
        }

        try:
            await self.redis.xadd("orders_stream", event_data)
            logger.info(
                "order_event_published", order_id=order_id, user_id=current_user.id
            )

            read_items = [
                ReadOrderItem(
                    product_id=i["product_id"],
                    quantity=i["quantity"],
                    unit_price=Decimal(str(i["unit_price"])),
                )
                for i in items_payload
            ]

            return ReadOrder(
                order_id=order_id,
                user_id=current_user.id,
                total_price=total_price,
                state=OrderState.processing,
                order_date=datetime.now(UTC),
                items=read_items,
            )

        except Exception as e:
            logger.error("stream_publish_failed_rolling_back", error=str(e))
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
