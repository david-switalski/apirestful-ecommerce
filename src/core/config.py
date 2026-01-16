from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    This class loads environment variables and provides strongly-typed
    access to configuration values such as project metadata, database URL,
    JWT settings, security parameters and cache parameters.
    """

    PROJECT_NAME: str = "APIRESTFUL E-COMMERCE"  # Name of the project
    PROJECT_VERSION: str = "1.0"  # Version of the project
    DATABASE_URL: str  # Database connection URL

    SECRET_KEY: str  # Secret key for JWT encoding/decoding
    ALGORITHM: str = "HS256"  # Algorithm used for JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Access token expiration time in minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh token expiration time in days

    ISSUER: str  # JWT issuer
    AUDIENCE: str  # JWT audience

    REDIS_USER: str  # User for Redis server. De
    REDIS_PASSWORD: str  # Password for Redis server
    REDIS_HOST: str  # Host address for Redis server
    REDIS_PORT: int  # Port number for Redis server
    REDIS_DB: int  # Database index for Redis server

    # Configuration for loading environment variables from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton instance of the Settings class to be used throughout the application
settings = Settings()
