import json
import secrets
import time
from datetime import UTC, datetime
from decimal import Decimal

import structlog
from opentelemetry import propagate
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
            total_price += Decimal(str(product.price)) * item.quantity

        result = await self.deduct_script(keys=keys, args=args)

        if result[0] == -1:
            missing_key = result[1]
            missing_id = int(missing_key.split(":")[1])

            p_to_refill = product_map[missing_id]
            await self.redis.set(missing_key, p_to_refill.stock, nx=True)

            result = await self.deduct_script(keys=keys, args=args)

        if result[0] == -2:
            failed_id = int(result[1].split(":")[1])
            raise InsufficientStockError(
                product_id=failed_id,
                product_name=product_map[failed_id].name,
                requested=next(
                    i.quantity for i in order_data.items if i.product_id == failed_id
                ),
                available=int(result[2]),
            )

        order_id = generate_order_id()
        items_payload = [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": str(product_map[i.product_id].price),
            }
            for i in order_data.items
        ]

        event_data = {
            "order_id": str(order_id),
            "user_id": str(current_user.id),
            "total_price": str(total_price),
            "items": json.dumps(items_payload),
        }

        headers: dict[str, str] = {}
        propagate.inject(headers)
        event_data["traceparent"] = headers.get("traceparent", "")

        try:
            await self.redis.xadd("orders_stream", event_data)
            return ReadOrder(
                order_id=order_id,
                user_id=current_user.id,
                total_price=total_price,
                state=OrderState.processing,
                order_date=datetime.now(UTC),
                items=[
                    ReadOrderItem(
                        product_id=i["product_id"],
                        quantity=i["quantity"],
                        unit_price=Decimal(str(i["unit_price"])),
                    )
                    for i in items_payload
                ],
            )
        except Exception as e:
            logger.error("order_publish_failed_rolling_back_stock", error=str(e))
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
