import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.users import User as UserModel
from src.services.authentication.service import get_password_hash

pytestmark = pytest.mark.anyio

@pytest.fixture
def test_user_credentials() -> dict:
    return {"username": "testuser", "password": "Password123$"} # pragma: allowlist secret

@pytest.fixture
async def created_test_user(client: AsyncClient, test_user_credentials: dict) -> dict:
    response = await client.post("/users/", json=test_user_credentials)
    assert response.status_code == 200
    return response.json()

@pytest.fixture
async def authenticated_user_client(client: AsyncClient, created_test_user: dict, test_user_credentials: dict) -> AsyncClient:
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"],
    }
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture
async def authenticated_admin_client(client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    admin_username = "adminuser"
    admin_password = "AdminPassword123$" # pragma: allowlist secret
    
    hashed_password = await get_password_hash(admin_password)
    admin_user = UserModel(
        username=admin_username,
        hashed_password=hashed_password,
        role="admin"
    )
    db_session.add(admin_user)
    await db_session.commit()

    login_data = {"username": admin_username, "password": admin_password}
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client

class TestUserCreationAndAuth:
    
    async def test_create_user(self, client: AsyncClient, db_session: AsyncSession, test_user_credentials: dict):
        response = await client.post("/users/", json=test_user_credentials)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_credentials["username"]
        assert "id" in data
        assert "password" not in data  

        user_in_db = await db_session.get(UserModel, data["id"])
        assert user_in_db is not None
        assert user_in_db.username == test_user_credentials["username"]

    async def test_create_user_already_exists(self, client: AsyncClient, created_test_user: dict, test_user_credentials: dict):
        response = await client.post("/users/", json=test_user_credentials)
        assert response.status_code == 409 

    async def test_login_for_access_token(self, client: AsyncClient, created_test_user: dict, test_user_credentials: dict):
        login_data = {
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"],
        }
        response = await client.post("/users/token", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, created_test_user: dict, test_user_credentials: dict):
        login_data = {
            "username": test_user_credentials["username"],
            "password": "wrongpassword", # pragma: allowlist secret
        }
        response = await client.post("/users/token", data=login_data)
        assert response.status_code == 401

    async def test_read_users_me(self, authenticated_user_client: AsyncClient, created_test_user: dict):
        response = await authenticated_user_client.get("/users/me/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == created_test_user["username"]
        assert data["id"] == created_test_user["id"]


class TestAdminActions:
    async def test_admin_can_read_all_users(self, authenticated_admin_client: AsyncClient, created_test_user: dict):
        response = await authenticated_admin_client.get("/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  
        usernames = [user["username"] for user in data]
        assert "adminuser" in usernames
        assert "testuser" in usernames

    async def test_normal_user_cannot_read_all_users(self, authenticated_user_client: AsyncClient):
        response = await authenticated_user_client.get("/users/")
        assert response.status_code == 403 

    async def test_admin_can_change_user_role(self, authenticated_admin_client: AsyncClient, created_test_user: dict, db_session: AsyncSession):
        username_to_change = created_test_user["username"]
        
        response = await authenticated_admin_client.patch(
            f"/users/admin/users/{username_to_change}/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

        user_in_db = await db_session.get(UserModel, created_test_user["id"])
        assert user_in_db.role == "admin"

    async def test_admin_cannot_demote_last_admin(self, authenticated_admin_client: AsyncClient):
        response = await authenticated_admin_client.patch(
            "/users/admin/users/adminuser/role",
            json={"role": "user"}
        )
        
        assert response.status_code == 400
        assert "The last administrator cannot be demoted" in response.json()["detail"]

    async def test_admin_can_delete_user(self, authenticated_admin_client: AsyncClient, created_test_user: dict, db_session: AsyncSession):
        user_id_to_delete = created_test_user["id"]
        
        response = await authenticated_admin_client.delete(f"/users/{user_id_to_delete}")
        
        assert response.status_code == 204 

        user_in_db = await db_session.get(UserModel, user_id_to_delete)
        assert user_in_db is None

    async def test_admin_cannot_delete_last_admin(self, authenticated_admin_client: AsyncClient, db_session: AsyncSession):
        query = select(UserModel).where(UserModel.username == "adminuser")
        result = await db_session.execute(query)
        admin_user = result.scalar_one()
        
        response = await authenticated_admin_client.delete(f"/users/{admin_user.id}")
        
        assert response.status_code == 400
        assert "The last administrator cannot be deleted" in response.json()["detail"]