import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.products import Product as ProductModel

pytestmark = pytest.mark.asyncio


@pytest.fixture
def product_data() -> dict:
    """Returns a dictionary with valid data to create a product."""
    return {
        "name": "Laptop Pro X",
        "category": "Electronics",
        "price": 1299.99,
        "stock": 50,
        "description": "A high-performance laptop for professionals.",
        "available": True,
    }

@pytest.fixture
async def created_product(db_session: AsyncSession, product_data: dict) -> ProductModel:
    """
    Fixture that creates a product directly in the database to be
    used in read, update, or delete tests.
    Returns the SQLAlchemy model instance.
    """
    product = ProductModel(**product_data)
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product

class TestPublicProductEndpoints:
    """
    Tests for product endpoints that are public (do not require authentication).
    """

    async def test_read_all_products(self, client: AsyncClient, created_product: ProductModel):
        """Checks that a list of products can be retrieved."""
        response = await client.get("/products/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Checks that the created product's name is in the returned product list
        assert created_product.name in [p["name"] for p in data]

    async def test_read_one_product(self, client: AsyncClient, created_product: ProductModel):
        """Checks that a specific product can be retrieved by its ID."""
        response = await client.get(f"/products/{created_product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_product.id
        assert data["name"] == created_product.name
        assert data["category"] == created_product.category

    async def test_read_nonexistent_product(self, client: AsyncClient):
        """Checks that a 404 is returned when requesting a non-existent product."""
        response = await client.get("/products/99999")

        assert response.status_code == 404


class TestAdminProductActions:
    """
    Tests for product endpoints that require admin privileges.
    """

    async def test_admin_can_create_product(
        self, authenticated_admin_client: AsyncClient, db_session: AsyncSession, product_data: dict
    ):
        """Checks that an admin can create a new product."""
        response = await authenticated_admin_client.post("/products/create_product", json=product_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product_data["name"]
        assert "id" in data

        product_in_db = await db_session.get(ProductModel, data["id"])
        assert product_in_db is not None
        assert product_in_db.name == product_data["name"]

    async def test_normal_user_cannot_create_product(
        self, authenticated_user_client: AsyncClient, product_data: dict
    ):
        """Checks that a normal user cannot create a product (gets 403 Forbidden)."""
        response = await authenticated_user_client.post("/products/create_product", json=product_data)
        
        assert response.status_code == 403

    async def test_admin_can_update_product(
        self, authenticated_admin_client: AsyncClient, created_product: ProductModel, db_session: AsyncSession
    ):
        """Checks that an admin can update an existing product."""
        update_data = {"name": "Laptop Pro X (Updated)", "price": 1399.00}
        
        response = await authenticated_admin_client.patch(f"/products/{created_product.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]

        await db_session.refresh(created_product)
        assert created_product.name == update_data["name"]

    async def test_normal_user_cannot_update_product(
        self, authenticated_user_client: AsyncClient, created_product: ProductModel
    ):
        """Checks that a normal user cannot update a product."""
        update_data = {"name": "Hacked Laptop"}
        
        response = await authenticated_user_client.patch(f"/products/{created_product.id}", json=update_data)
        
        assert response.status_code == 403

    async def test_admin_can_delete_product(
        self, authenticated_admin_client: AsyncClient, created_product: ProductModel, db_session: AsyncSession
    ):
        """Checks that an admin can delete a product."""
        product_id = created_product.id
        
        response = await authenticated_admin_client.delete(f"/products/{product_id}")

        assert response.status_code == 204  # No Content

        product_in_db = await db_session.get(ProductModel, product_id)
        assert product_in_db is None

    async def test_normal_user_cannot_delete_product(
        self, authenticated_user_client: AsyncClient, created_product: ProductModel
    ):
        """Checks that a normal user cannot delete a product."""
        response = await authenticated_user_client.delete(f"/products/{created_product.id}")
        
        assert response.status_code == 403 # Fordibben