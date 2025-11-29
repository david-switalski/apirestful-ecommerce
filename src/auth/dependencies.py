from typing import Annotated
from typing import Any
from typing import Coroutine

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from src.core.config import settings
from src.models.users import User as UserModel
from src.repositories.user_repository import UserRepository
from src.schemas.users import TokenData
from src.services.authentication.service import AuthenticationService
from src.users.dependencies import get_authentication_service
from src.users.dependencies import get_user_repository

# OAuth2 scheme for extracting the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserModel:
    """
    Retrieve the current user based on the JWT access token.

    Args:
        token (str): JWT access token extracted from the request.
        db (Db_session): Database session dependency.

    Returns:
        UserModel: The authenticated user object.

    Raises:
        HTTPException: If the token is invalid, expired, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token and validate claims
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            audience=settings.AUDIENCE,
            issuer=settings.ISSUER,
            algorithms=[settings.ALGORITHM],
        )

        # Ensure the token type is 'access'
        if payload.get("type") != "access":
            raise credentials_exception

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except jwt.ExpiredSignatureError:
        # Token has expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidTokenError:
        # Token is invalid
        raise credentials_exception

    # Retrieve the user from the database
    user = await user_repo.get_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    """
    Ensure the current user is active.

    Args:
        current_user (UserModel): The authenticated user object.

    Returns:
        UserModel: The active user object.

    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.available:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return current_user


def require_role(required_role: str) -> Coroutine[Any, Any, UserModel]:
    """
    Dependency factory to require a specific user role.

    Args:
        required_role (str): The required role for access.

    Returns:
        Callable: Dependency function that checks the user's role.

    Raises:
        HTTPException: If the user does not have the required role.
    """

    async def role_checker(
        current_user: Annotated[UserModel, Depends(get_current_active_user)],
    ) -> UserModel:
        """
        Check if the current user has the required role.

        Args:
            current_user (UserModel): The active user object.

        Returns:
            UserModel: The user object if the role matches.

        Raises:
            HTTPException: If the user's role does not match the required role.
        """
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access Forbidden"
            )

        return current_user

    return role_checker  # type: ignore[return-value]


# Dependency that provides the authentication service
Auth_user = Annotated[AuthenticationService, Depends(get_authentication_service)]

# Dependency that provides the currently authenticated and active user
Current_user = Annotated[UserModel, Depends(get_current_active_user)]

# Annotated dependency for requiring an admin user role
Admin_user = Annotated[UserModel, Depends(require_role("admin"))]
