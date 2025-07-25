from src.data_base.session import get_db
from src.schemas.products import ReadProduct, CreateProduct, UpdateProduct
from fastapi import APIRouter, Depends, HTTPException, status
from src.models.products import Product as ProductModel
from sqlalchemy import select


router = APIRouter(prefix = "/products")

@router.get("/", tags = "Products", response_model=list[ReadProduct])
async def read_all_products(db = Depends(get_db)):
    stmt = select(ProductModel)
    result = await db.execute(stmt)
    
    products = result.scalars().all()
    
    return  products
    
    
@router.get("/{product_id}", tags = "Products", response_model=ReadProduct)
async def read_product(product_id : int, db = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    
    result = await db.execute(stmt)
    
    product = result.scalars().first()
    
    if product is not None:
        return  product
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@router.post("/create_product", tags="Products", response_model=ReadProduct)
async def create_product(product : CreateProduct, db = Depends(get_db)):
    model = ProductModel(**product.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return model

@router.patch("/{product_id}", tags="Product", response_model=ReadProduct)
async def update_product(product_id : int, product : UpdateProduct, db = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    
    result = await db.execute(stmt)
    
    product_db = result.scalars().first()
    
    if product_db is not None:
        update_data = product.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(product_db, key, value) 
        
        await db.commit()
        await db.refresh(product_db)
        
        return product_db
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@router.delete("/{product_id}", tags="Products", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id : int, db = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    
    result = await db.execute(stmt)
    
    deleted_product = result.scalars().first()
    
    if deleted_product is not None:
        db.delete(deleted_product)
        await db.commit()
        
        return None
        
    else:
        raise HTTPException(status_code=404, detail="Product not found")
    
    

