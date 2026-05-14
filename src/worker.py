import asyncio
import json
import os
from decimal import Decimal

import structlog
from opentelemetry import propagate, trace
from opentelemetry.trace import SpanKind
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.observability import setup_tracing
from src.models.orders import Order as OrderModel
from src.models.orders import OrderItem, OrderState
from src.models.products import Product

logger = structlog.get_logger()

engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=50)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

setup_tracing("order-worker")


async def process_orders() -> None:
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    stream_name = "orders_stream"
    group_name = "order_processors"
    consumer_name = f"worker-{os.getpid()}"

    try:
        await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        logger.info("consumer_group_created", group=group_name)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise

    logger.info("worker_started", consumer=consumer_name)

    while True:
        try:
            messages = await redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=10,
                block=5000,
            )

            if not messages:
                continue

            for _stream, message_list in messages:
                for message_id, event_data in message_list:
                    await handle_order_event(event_data)

                    await redis.xack(stream_name, group_name, message_id)
                    logger.info("message_acked", message_id=message_id)

        except Exception as e:
            logger.error("worker_error", error=str(e))
            await asyncio.sleep(1)


async def handle_order_event(event_data: dict) -> None:
    context = propagate.extract({"traceparent": event_data.get("traceparent")})
    tracer = trace.get_tracer("order-worker")

    order_id = int(event_data["order_id"])
    items_data = json.loads(event_data["items"])

    order_items = [
        OrderItem(
            product_id=i["product_id"],
            quantity=i["quantity"],
            unit_price=Decimal(i["unit_price"]),
        )  # type: ignore[call-arg]
        for i in items_data
    ]

    new_order = OrderModel(
        order_id=order_id,
        user_id=int(event_data["user_id"]),
        total_price=Decimal(event_data["total_price"]),
        state=OrderState.processing,
        items=order_items,
    )  # type: ignore[call-arg]

    with tracer.start_as_current_span(
        "process_order_worker", context=context, kind=SpanKind.CONSUMER
    ):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    session.add(new_order)

                    for item in items_data:
                        product = await session.get(Product, item["product_id"])
                        if product:
                            product.stock -= item["quantity"]
                logger.info("order_saved_to_db", order_id=order_id)
            except IntegrityError:
                logger.warning(
                    "order_already_exists_idempotency_hit", order_id=order_id
                )


if __name__ == "__main__":
    asyncio.run(process_orders())
