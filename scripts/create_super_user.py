import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.security import get_password_hash
from src.models.users import User as UserModel
from src.models.users import UserRole
from src.repositories.user_repository import UserRepository
from src.services.users.service import UserService

# Load environment variables from .env file
load_dotenv()

# Constants for the admin user credentials
ADMIN_USER = os.getenv("ADMIN_USER", "SuperUser")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Test12345$")  # pragma: allowlist secret
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("CRITICAL ERROR: The DATABASE_URL environment variable is not set.")
    exit(1)

# Create the asynchronous SQLAlchemy engine and session factory
engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def create_admin_user():
    """
    Asynchronously creates an administrator user in the database if it does not already exist.
    - Checks if the admin user exists by username.
    - If not, hashes the password and creates a new admin user with the specified role.
    - Commits the new user to the database.
    """
    print("Starting script to create an administrator user...")
    async with SessionLocal() as session:
        async with session.begin():

            user_repo = UserRepository(session)

            user_service = UserService(user_repo)

            # Check if the admin user already exists
            user = await user_service.get_user_by_username(ADMIN_USER)

            if user is None:
                # Hash the admin password
                hash_password = get_password_hash(ADMIN_PASSWORD)

                # Create a new admin user instance
                new_admin = UserModel(
                    username=ADMIN_USER,
                    hashed_password=hash_password,
                    role=UserRole.admin,
                )

                session.add(new_admin)
                await session.flush()
                await session.refresh(new_admin)

                print(f"SuperUsuario {ADMIN_USER} create")
            else:
                print("The user already exists")


if __name__ == "__main__":
    """
    Entry point for the script. Runs the create_admin_user coroutine.
    """
    import asyncio

    asyncio.run(create_admin_user())
