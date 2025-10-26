# En tests/test_orders.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from src.models.products import Product as ProductModel
from src.models.orders import Order as OrderModel

pytestmark = pytest.mark.asyncio

class TestOrderCreation:
    async def test_create_order_success(
        self,
        authenticated_user_client: AsyncClient,
        db_session: AsyncSession,
        created_test_user: dict,
        product_in_db: ProductModel,
        another_product_in_db: ProductModel
    ):
        order_data = {
            "items": [
                {"product_id": product_in_db.id, "quantity": 2},      
                {"product_id": another_product_in_db.id, "quantity": 5} 
            ]
        }
        expected_total = Decimal("47.50")
        initial_stock_1 = product_in_db.stock
        initial_stock_2 = another_product_in_db.stock

        response = await authenticated_user_client.post("/orders/", json=order_data)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["user_id"] == created_test_user["id"]
        assert Decimal(response_data["total_price"]) == expected_total
        assert len(response_data["items"]) == 2
        assert response_data["state"] == "pending"

        await db_session.refresh(product_in_db)
        await db_session.refresh(another_product_in_db)
        assert product_in_db.stock == initial_stock_1 - 2
        assert another_product_in_db.stock == initial_stock_2 - 5
        
        order_in_db = await db_session.get(OrderModel, response_data["order_id"])
        assert order_in_db is not None
        assert order_in_db.total_price == expected_total
        assert len(order_in_db.items) == 2