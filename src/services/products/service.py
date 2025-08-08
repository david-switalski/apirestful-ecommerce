from sqlalchemy import select
from src.models.products import Product as ProductModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.products import CreateProduct, UpdateProduct


async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalars().first()
    
    return product

async def get_all_products(db: AsyncSession, limit, offset):
    result = await db.execute(select(ProductModel).limit(limit).offset(offset))
    all_products = result.scalars().all()
    
    return  all_products

async def get_created_product(product: CreateProduct, db: AsyncSession):
    created_product = ProductModel(**product.model_dump())
    db.add(created_product)
    await db.commit()
    await db.refresh(created_product)
    
    return created_product

async def get_updated_product(id: int, product: UpdateProduct, db: AsyncSession):
    result = await db.execute(select(ProductModel).where(ProductModel.id == id))
    updated_product = result.scalars().first()
    
    if updated_product is not None:
        update_data = product.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(updated_product, key, value) 
        
        await db.commit()
        await db.refresh(updated_product)
        
    return updated_product    

        
async def get_deleted_product(id: int, db: AsyncSession):
    result = await db.execute(select(ProductModel).where(ProductModel.id == id))
    deleted_product = result.scalars().first()
    
    if deleted_product is not None:
        await db.delete(deleted_product)
        await db.commit()
        
    return deleted_product