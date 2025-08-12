import os 
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.auth.dependencies import get_user
from src.services.authentication.service import get_password_hash
from src.models.users import User as UserModel, UserRole

load_dotenv()

ADMIN_USER = "SuperUser"
ADMIN_PASSWORD = "Test12345$" # pragma: allowlist secret

local_db_url = os.getenv("DATABASE_URL_ALEMBIC")

if not local_db_url:
    print("ERROR: The DATABASE_URL_ALEMBIC enviroment variable is not defined in the .env file")
    exit()
    
engine = create_async_engine(local_db_url)
SessionLocal = async_sessionmaker(autocommit = False, autoflush = False, bind = engine)   

async def create_admin_user():
    print("Starting script to create an administrator user...")
    async with SessionLocal() as session:
        
        user = await get_user(ADMIN_USER, session)
            
        if user is None:
            hash_password = await get_password_hash(ADMIN_PASSWORD)
                
            new_admin = UserModel(username = ADMIN_USER, hashed_password = hash_password, role=UserRole.admin)
                
            session.add(new_admin)
            await session.commit()
            
            await session.refresh(new_admin)
            
            print(f'SuperUsuario {ADMIN_USER} create')
        else:
            print("The user already exists")
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(create_admin_user())