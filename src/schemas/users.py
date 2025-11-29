import re
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator
from pydantic import SecretStr

from src.models.users import UserRole


class UserValidations(BaseModel):
    """
    Base schema for user validation.
    Validates username and password fields with custom rules.
    """

    username: str
    password: SecretStr

    @field_validator("username")
    def username_length(cls, v):
        """
        Validates that the username length is between 3 and 50 characters.
        """
        if v is not None and (len(v) < 3 or len(v) > 50):
            raise ValueError("Username must be between 3 and 50 characters")
        return v

    @field_validator("password")
    def password_validation(cls, v):
        """
        Validates that the password is between 8 and 50 characters and contains at least
        one uppercase letter, one lowercase letter, one digit, and one special character.
        """
        if v is not None:
            regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,50}$"
            if not re.search(regex, v.get_secret_value()):
                raise ValueError(
                    "Password must be between 8 and 50 characters and contain at least one uppercase letter, one lowercase letter, one integer, and one special character."
                )
        return v


class CreateUser(UserValidations):
    """
    Schema for creating a new user.
    Inherits username and password validation.
    """

    available: bool = True


class UpdateUser(UserValidations):
    """
    Schema for updating user information.
    All fields are optional to allow partial updates.
    """

    username: str | None = None
    available: bool | None = None
    password: SecretStr | None = None


class ReadUser(BaseModel):
    """
    Schema for reading a single user's information.
    Includes user id, username, availability, role, and timestamps.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    username: str
    available: bool
    role: UserRole
    created_at: datetime | None
    updated_at: datetime | None


class ReadAllUsers(BaseModel):
    """
    Schema for reading a list of users with basic information.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    username: str
    available: bool


class UserRoleCurrent(BaseModel):
    """
    Schema for representing the current user's role.
    """

    role: UserRole


class Token(BaseModel):
    """
    Schema for JWT tokens.
    Contains access and refresh tokens and token type.
    """

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema for token payload data.
    """

    username: str | None = None


class RefreshTokenRequest(BaseModel):
    """
    Schema for requesting a new access token using a refresh token.
    """

    refresh_token: str
