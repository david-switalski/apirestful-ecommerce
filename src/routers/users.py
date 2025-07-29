from src.data_base.session import get_db
from src.schemas.users import ReadUser, CreateUser, UpdateUser
from fastapi import APIRouter, Depends, HTTPException, status
from src.models.users import User as UserModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix = "/users")

@router.get("/", tags = ["Users"], response_model=list[ReadUser])
async def read_all_users(db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel)
    result = await db.execute(stmt)
    
    users = result.scalars().all()
    
    return  users
    
    
@router.get("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def read_user(user_id : int, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.id == user_id)
    
    result = await db.execute(stmt)
    
    user = result.scalars().first()
    
    if user is not None:
        return  user
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/", tags = ["Users"], response_model=ReadUser)
async def create_user(user : CreateUser, db: AsyncSession = Depends(get_db)):
    model = UserModel(**user.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return model

@router.patch("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def update_user(user_id : int, user : UpdateUser, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.id == user_id)
    
    result = await db.execute(stmt)
    
    user_db = result.scalars().first()
    
    if user_db is not None:
        update_data = user.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(user_db, key, value) 
        
        await db.commit()
        await db.refresh(user_db)
        
        return user_db
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_id}", tags = ["Users"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id : int, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.id == user_id)
    
    result = await db.execute(stmt)
    
    deleted_user = result.scalars().first()
    
    if deleted_user is not None:
        await db.delete(deleted_user)
        await db.commit()
        
        return None
        
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
    

