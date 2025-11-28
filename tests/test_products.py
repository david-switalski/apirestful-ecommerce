import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis
from src.models.products import Product as ProductModel
from src.schemas.products import ReadProduct

pytestmark = pytest.mark.asyncio


@pytest.fixture
def product_data() -> dict:
    """Returns valid data to create a product."""
    return {
        "name": "Laptop Pro X",
        "category": "Electronics",
        "price": 1299.99,
        "stock": 16,
        "description": "A high-performance laptop for professionals.",
        "available": True,
    }


@pytest.fixture
async def created_product(db_session: AsyncSession, product_data: dict) -> ProductModel:
    """Creates a product directly in the DB for tests."""
    product = ProductModel(**product_data)
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


class TestPublicProductEndpoints:
    """Tests for public product endpoints (no auth required)."""

    async def test_read_all_products(
        self, client: AsyncClient, created_product: ProductModel
    ):
        """Checks that a list of products can be retrieved."""
        response = await client.get("/products/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert created_product.name in [p["name"] for p in data]

    async def test_read_one_product(
        self, client: AsyncClient, created_product: ProductModel
    ):
        """Checks that a specific product can be retrieved by its ID."""
        response = await client.get(f"/products/{created_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_product.id
        assert data["name"] == created_product.name

    async def test_read_nonexistent_product(self, client: AsyncClient):
        """Checks that a 404 is returned for a non-existent product."""
        response = await client.get("/products/99999")
        assert response.status_code == 404


class TestAdminProductActions:
    """Tests for product endpoints requiring admin privileges."""

    async def test_admin_can_create_product(
        self,
        authenticated_admin_client: AsyncClient,
        db_session: AsyncSession,
        product_data: dict,
    ):
        """Checks that an admin can create a new product."""
        response = await authenticated_admin_client.post(
            "/products/create_product", json=product_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == product_data["name"]
        product_in_db = await db_session.get(ProductModel, data["id"])
        assert product_in_db is not None

    async def test_normal_user_cannot_create_product(
        self, authenticated_user_client: AsyncClient, product_data: dict
    ):
        """Checks that a normal user gets a 403 Forbidden error."""
        response = await authenticated_user_client.post(
            "/products/create_product", json=product_data
        )
        assert response.status_code == 403

    async def test_admin_can_update_product(
        self,
        authenticated_admin_client: AsyncClient,
        created_product: ProductModel,
        db_session: AsyncSession,
    ):
        """Checks that an admin can update an existing product."""
        update_data = {"name": "Laptop Pro X (Updated)", "price": 1399.00}
        response = await authenticated_admin_client.patch(
            f"/products/{created_product.id}", json=update_data
        )
        assert response.status_code == 200
        await db_session.refresh(created_product)
        assert created_product.name == update_data["name"]

    async def test_admin_can_delete_product(
        self,
        authenticated_admin_client: AsyncClient,
        created_product: ProductModel,
        db_session: AsyncSession,
    ):
        """Checks that an admin can delete a product."""
        product_id = created_product.id
        response = await authenticated_admin_client.delete(f"/products/{product_id}")
        assert response.status_code == 204
        product_in_db = await db_session.get(ProductModel, product_id)
        assert product_in_db is None


class TestProductCaching:
    """Specific tests for Redis caching logic."""

    async def test_read_product_populates_cache(
        self,
        client: AsyncClient,
        created_product: ProductModel,
        test_redis_client: Redis,
    ):
        """Test that accessing a product for the first time adds it to the cache."""
        product_id = created_product.id
        cache_key = f"product:{product_id}"

        assert await test_redis_client.get(cache_key) is None

        response = await client.get(f"/products/{product_id}")
        assert response.status_code == 200

        cached_data = await test_redis_client.get(cache_key)
        assert cached_data is not None
        cached_product = json.loads(cached_data)
        assert cached_product["id"] == product_id
        assert cached_product["name"] == created_product.name

    async def test_read_product_hits_cache(
        self,
        client: AsyncClient,
        created_product: ProductModel,
        test_redis_client: Redis,
    ):
        """Test that a cached product is served from Redis, not the DB."""
        product_id = created_product.id
        cache_key = f"product:{product_id}"

        cached_dummy_data = ReadProduct.model_validate(created_product).model_dump()
        cached_dummy_data["name"] = "CACHED NAME"
        await test_redis_client.set(
            cache_key, json.dumps(cached_dummy_data, default=str)
        )

        response = await client.get(f"/products/{product_id}")
        assert response.status_code == 200

        assert response.json()["name"] == "CACHED NAME"

    async def test_update_product_invalidates_cache(
        self,
        authenticated_admin_client: AsyncClient,
        created_product: ProductModel,
        test_redis_client: Redis,
    ):
        """Test that updating a product removes its old entry from the cache."""
        product_id = created_product.id
        cache_key = f"product:{product_id}"

        await authenticated_admin_client.get(f"/products/{product_id}")
        assert await test_redis_client.get(cache_key) is not None

        update_data = {"price": 99.99}
        await authenticated_admin_client.patch(
            f"/products/{product_id}", json=update_data
        )

        assert await test_redis_client.get(cache_key) is None

    async def test_delete_product_invalidates_cache(
        self,
        authenticated_admin_client: AsyncClient,
        created_product: ProductModel,
        test_redis_client: Redis,
    ):
        """Test that deleting a product removes it from the cache."""
        product_id = created_product.id
        cache_key = f"product:{product_id}"

        await authenticated_admin_client.get(f"/products/{product_id}")
        assert await test_redis_client.get(cache_key) is not None

        await authenticated_admin_client.delete(f"/products/{product_id}")

        assert await test_redis_client.get(cache_key) is None
