# En tests/test_orders.py

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.products import Product as ProductModel

pytestmark = pytest.mark.asyncio


class TestOrderCreation:
    async def test_create_order_success(
        self,
        authenticated_user_client: AsyncClient,
        db_session: AsyncSession,
        test_redis_client: Redis,
        created_test_user: dict,
        product_in_db: ProductModel,
        another_product_in_db: ProductModel,
    ):
        order_data = {
            "items": [
                {"product_id": product_in_db.id, "quantity": 2},
                {"product_id": another_product_in_db.id, "quantity": 5},
            ]
        }

        response = await authenticated_user_client.post("/orders/", json=order_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["state"] == "processing"

        messages = await test_redis_client.xrange("orders_stream")
        assert len(messages) == 1
        event_data = messages[0][1]

        assert int(event_data["order_id"]) == response_data["order_id"]
        assert int(event_data["user_id"]) == created_test_user["id"]
