import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.users import User as UserModel

pytestmark = pytest.mark.anyio

class TestUserCreationAndAuth:
    """
    Test suite for user registration, authentication, and self-access endpoints.
    """

    async def test_create_user(self, client: AsyncClient, db_session: AsyncSession, test_user_credentials: dict):
        """
        Test that a new user can be created successfully and is stored in the database.
        """
        response = await client.post("/users/", json=test_user_credentials)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_credentials["username"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned in response

        # Verify user exists in the database
        user_in_db = await db_session.get(UserModel, data["id"])
        assert user_in_db is not None
        assert user_in_db.username == test_user_credentials["username"]

    async def test_create_user_already_exists(self, client: AsyncClient, created_test_user: dict, test_user_credentials: dict):
        """
        Test that creating a user with an existing username returns a 409 conflict.
        """
        response = await client.post("/users/", json=test_user_credentials)
        assert response.status_code == 409 

    async def test_login_for_access_token(self, client: AsyncClient, created_test_user: dict, test_user_credentials: dict):
        """
        Test that a user can log in and receive access and refresh tokens.
        """
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
        """
        Test that login fails with a wrong password and returns 401 unauthorized.
        """
        login_data = {
            "username": test_user_credentials["username"],
            "password": "wrongpassword", # pragma: allowlist secret
        }
        response = await client.post("/users/token", data=login_data)
        assert response.status_code == 401

    async def test_read_users_me(self, authenticated_user_client: AsyncClient, created_test_user: dict):
        """
        Test that an authenticated user can retrieve their own user information.
        """
        response = await authenticated_user_client.get("/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == created_test_user["username"]
        assert data["id"] == created_test_user["id"]


class TestAdminActions:
    """
    Test suite for admin-only user management actions.
    """

    async def test_admin_can_read_all_users(self, authenticated_admin_client: AsyncClient, created_test_user: dict):
        """
        Test that an admin can retrieve a list of all users.
        """
        response = await authenticated_admin_client.get("/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Should include at least admin and test user
        usernames = [user["username"] for user in data]
        assert "adminuser" in usernames
        assert "testuser" in usernames

    async def test_normal_user_cannot_read_all_users(self, authenticated_user_client: AsyncClient):
        """
        Test that a normal user cannot access the list of all users (forbidden).
        """
        response = await authenticated_user_client.get("/users/")
        assert response.status_code == 403 

    async def test_admin_can_change_user_role(self, authenticated_admin_client: AsyncClient, created_test_user: dict, db_session: AsyncSession):
        """
        Test that an admin can change another user's role.
        """
        username_to_change = created_test_user["username"]
        
        response = await authenticated_admin_client.patch(
            f"/users/admin/users/{username_to_change}/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

        # Verify role change in the database
        user_in_db = await db_session.get(UserModel, created_test_user["id"])
        assert user_in_db.role == "admin"

    async def test_admin_cannot_demote_last_admin(self, authenticated_admin_client: AsyncClient):
        """
        Test that the last admin cannot be demoted to a non-admin role.
        """
        response = await authenticated_admin_client.patch(
            "/users/admin/users/adminuser/role",
            json={"role": "user"}
        )
        
        assert response.status_code == 400
        assert "The last administrator cannot be demoted" in response.json()["detail"]

    async def test_admin_can_delete_user(self, authenticated_admin_client: AsyncClient, created_test_user: dict, db_session: AsyncSession):
        """
        Test that an admin can delete a user and the user is removed from the database.
        """
        user_id_to_delete = created_test_user["id"]
        
        response = await authenticated_admin_client.delete(f"/users/{user_id_to_delete}")
        
        assert response.status_code == 204 

        # Verify user is deleted from the database
        user_in_db = await db_session.get(UserModel, user_id_to_delete)
        assert user_in_db is None

    async def test_admin_cannot_delete_last_admin(self, authenticated_admin_client: AsyncClient, db_session: AsyncSession):
        """
        Test that the last admin cannot be deleted from the system.
        """
        query = select(UserModel).where(UserModel.username == "adminuser")
        result = await db_session.execute(query)
        admin_user = result.scalar_one()
        
        response = await authenticated_admin_client.delete(f"/users/{admin_user.id}")
        
        assert response.status_code == 400
        assert "The last administrator cannot be deleted" in response.json()["detail"]