import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from passlib.context import CryptContext

from src.core.config import settings
from src.core.security import get_password_hash
from src.core.security import verify_password
from src.models.users import User as UserModel
from src.schemas.users import RefreshTokenRequest
from src.schemas.users import Token
from src.services.users.service import UserService


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def create_refresh_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            data (dict): Data to encode in the token.
            expires_delta (timedelta, optional): Expiration time for the token.

        Returns:
            str: The encoded JWT refresh token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "iss": settings.ISSUER,
                "aud": settings.AUDIENCE,
                "jti": str(uuid.uuid4()),
            }
        )
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data (dict): Data to encode in the token.
            expires_delta (timedelta, optional): Expiration time for the token.

        Returns:
            str: The encoded JWT access token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "iss": settings.ISSUER,
                "aud": settings.AUDIENCE,
                "jti": str(uuid.uuid4()),
            }
        )
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> UserModel:
        """
        Authenticate a user by username and password.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            UserModel: The authenticated user.

        Raises:
            HTTPException: If authentication fails.
        """
        user = await self.user_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        if verify_password(password, user.hashed_password):
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_login_for_access_token(
        self, form_data: OAuth2PasswordRequestForm
    ) -> Token:
        """
        Authenticate user and generate access and refresh tokens.

        Args:
            form_data (OAuth2PasswordRequestForm): The login form data.

        Returns:
            Token: The access and refresh tokens.

        Raises:
            HTTPException: If authentication fails.
        """
        user = await self.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_refresh_token = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = await self.create_access_token(
            data={"sub": user.username, "type": "access"},
            expires_delta=access_token_expire,
        )

        refresh_token = await self.create_refresh_token(
            data={"sub": user.username, "type": "refresh"},
            expires_delta=access_refresh_token,
        )

        # Store the hashed refresh token in the database
        user.hashed_refresh_token = get_password_hash(refresh_token)

        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    async def get_refresh_access_token(
        self,
        request: RefreshTokenRequest,
        credentials_exception: HTTPException,
    ) -> Token:
        """
        Generate new access and refresh tokens using a valid refresh token.

        Args:
            request (RefreshTokenRequest): The refresh token request.
            credentials_exception (HTTPException): Exception to raise on failure.

        Returns:
            Token: The new access and refresh tokens.

        Raises:
            HTTPException: If the refresh token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                request.refresh_token,
                settings.SECRET_KEY,
                audience=settings.AUDIENCE,
                issuer=settings.ISSUER,
                algorithms=[settings.ALGORITHM],
            )

            if payload.get("type") != "refresh":
                raise credentials_exception

            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception

            user = await self.user_service.get_user_by_username(username)
            if user is None or user.hashed_refresh_token is None:
                raise credentials_exception

            username_for_token = user.username

            is_valid_refresh_token = verify_password(
                request.refresh_token, user.hashed_refresh_token
            )
            if not is_valid_refresh_token:
                raise credentials_exception

            new_refresh_token = await self.create_refresh_token(
                data={"sub": username_for_token, "type": "refresh"}
            )
            user.hashed_refresh_token = get_password_hash(new_refresh_token)

            new_access_token = await self.create_access_token(
                data={"sub": username_for_token, "type": "access"}
            )

            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
            )

        except InvalidTokenError:
            raise credentials_exception

    async def logout(self, user_to_logout: UserModel) -> None:
        """
        Invalidates the user's refresh token to log them out.

        Sets the user's stored hashed refresh token to None in the database.

        Args:
            user_to_logout (UserModel): The user model instance for the user.

        Returns:
            None: Updates user data in the database.
        """
        user_to_logout.hashed_refresh_token = None
        await self.user_service.repo.update(user_to_logout)
