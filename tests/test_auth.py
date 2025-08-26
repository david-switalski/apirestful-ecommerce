import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User as UserModel

pytestmark = pytest.mark.anyio

@pytest.fixture
async def logged_in_user_tokens(client: AsyncClient, created_test_user: dict, test_user_credentials: dict) -> dict:
    """
    Fixture that logs in as a test user and returns the full token dictionary (access and refresh).
    """
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"],
    }
    response = await client.post("/users/token", data=login_data)
    assert response.status_code == 200
    return response.json()

@pytest.fixture
async def inactive_user_client(client: AsyncClient, db_session: AsyncSession, logged_in_user_tokens: dict, created_test_user: dict) -> AsyncClient:
    """
    Creates a user, logs in to obtain a token, then marks the user as inactive
    in the database and returns the client with the token (now invalid).
    """
    user_in_db = await db_session.get(UserModel, created_test_user["id"])
    user_in_db.available = False
    await db_session.commit()

    # Configure the client with the access token obtained BEFORE deactivating the user.
    access_token = logged_in_user_tokens["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client

class TestAccessToken:
    """Tests related to the creation and use of access tokens."""

    async def test_get_me_with_valid_token(self, authenticated_user_client: AsyncClient, created_test_user: dict):
        """Checks that a valid access token allows access to a protected route."""
        response = await authenticated_user_client.get("/users/me/")

        assert response.status_code == 200
        assert response.json()["username"] == created_test_user["username"]

    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """Checks that a malformed or invalid access token is rejected."""
        client.headers["Authorization"] = "Bearer not-a-real-token"

        response = await client.get("/users/me/")

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    async def test_get_me_without_token(self, client: AsyncClient):
        """Checks that access to a protected route without a token is rejected."""
        response = await client.get("/users/me/")

        assert response.status_code == 401


class TestRefreshTokenAndLogout:
    """Tests for the token refresh mechanism and logout."""

    async def test_refresh_token_successfully(self, client: AsyncClient, logged_in_user_tokens: dict):
        """Checks that a valid refresh token can be used to obtain a new pair of tokens."""
        original_refresh_token = logged_in_user_tokens["refresh_token"]
        original_access_token = logged_in_user_tokens["access_token"]
        
        response = await client.post("/users/token/refresh", json={"refresh_token": original_refresh_token})

        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # Checks that the new tokens are different from the originals
        assert new_tokens["access_token"] != original_access_token
        assert new_tokens["refresh_token"] != original_refresh_token

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Checks that an invalid refresh token is rejected."""
        response = await client.post("/users/token/refresh", json={"refresh_token": "not-a-real-refresh-token"})

        assert response.status_code == 401

    async def test_logout_invalidates_refresh_token(
        self, authenticated_user_client: AsyncClient, db_session: AsyncSession, created_test_user: dict
    ):
        """
        Checks that the logout endpoint works and clears the hashed_refresh_token in the DB.
        """
        response = await authenticated_user_client.post("/users/logout")

        assert response.status_code == 200
        assert response.json() == {'message': 'Logout success'}

        user_in_db = await db_session.get(UserModel, created_test_user["id"])
        assert user_in_db.hashed_refresh_token is None

    async def test_cannot_use_refresh_token_after_logout(self, client: AsyncClient, logged_in_user_tokens: dict):
        """
        Checks that a refresh token cannot be used after the user has logged out.
        """
        original_refresh_token = logged_in_user_tokens["refresh_token"]
        access_token = logged_in_user_tokens["access_token"]
        
        client.headers["Authorization"] = f"Bearer {access_token}"
        logout_response = await client.post("/users/logout")
        assert logout_response.status_code == 200

        response = await client.post("/users/token/refresh", json={"refresh_token": original_refresh_token})

        assert response.status_code == 401


class TestAuthorization:
    """Tests for authorization logic (permissions)."""

    async def test_inactive_user_cannot_access_protected_route(self, inactive_user_client: AsyncClient):
        """
        Checks that a user marked as inactive cannot access protected routes,
        even with a token that was valid in the past.
        """
        response = await inactive_user_client.get("/users/me/")

        assert response.status_code == 401
        assert response.json()["detail"]