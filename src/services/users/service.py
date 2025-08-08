from sqlalchemy import select
from src.models.users import User as UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.users import CreateUser, UpdateUser
from src.services.authentication.service import get_password_hash

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().first()
    return user

async def get_all_users(db: AsyncSession, limit, offset):
    result = await db.execute(select(UserModel).limit(limit).offset(offset))
    users = result.scalars()
    return users

async def get_user_me(db: AsyncSession, current_user):
    result = await db.execute(select(UserModel).where(UserModel.id == current_user.id))
    user = result.scalars().first()
    return user

async def get_create_user(user: CreateUser, db: AsyncSession):
    
    user_data = user.model_dump(exclude={'password'})
    
    plain_password = user.password.get_secret_value()
    
    hashed_pass = await get_password_hash(plain_password)
    
    model= UserModel(**user_data, hashed_password=hashed_pass)
    
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return model

async def get_updated_user(id: int, user:UpdateUser, db:AsyncSession):
    result = await db.execute(select(UserModel).where(UserModel.id == id))
    user_db = result.scalars().first()

    if user_db is not None:
        update_data = user.model_dump(exclude_unset=True)
        
        
        if "password" in update_data:
            update_data["hashed_password"] = await get_password_hash(user.password.get_secret_value())
            del update_data["password"]

        for key, value in update_data.items():
            setattr(user_db, key, value) 
        
        await db.commit()
        await db.refresh(user_db)
        
    return user_db
    
    
async def get_deleted_user(id: int, db: AsyncSession):
    result = await db.execute(select(UserModel).where(UserModel.id == id))
    
    deleted_user = result.scalars().first()
    
    if deleted_user is not None:
        await db.delete(deleted_user)
        await db.commit()
        
    return deleted_user