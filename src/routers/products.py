from src.data_base.dependencies import Db_session
from src.schemas.products import ReadProduct, CreateProduct, UpdateProduct, ReadAllProducts
from fastapi import APIRouter, HTTPException, status

from src.services.products.service import get_product_by_id, get_all_products, get_created_product, get_deleted_product, get_updated_product
from src.routers.users import Admin_user

router = APIRouter(prefix = "/products")

    
@router.get("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def read_product(db: Db_session, product_id : int):
    product = await get_product_by_id(db, product_id )
    
    if product is not None:
        return  product
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

@router.get("/", tags=["Products"], response_model=list[ReadAllProducts])
async def read_all_products(db: Db_session, limit: int=20, offset: int=0):
    
    all_products = await get_all_products(db, limit=limit, offset=offset)
    
    return all_products

@router.post("/create_product", tags=["Products"], response_model=ReadProduct)
async def create_product(product : CreateProduct, db: Db_session, admin_user: Admin_user):
    created_product = await get_created_product(product, db)
    
    if created_product is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product creation failed."
        )

    return created_product

@router.patch("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def update_product(product_id : int, product : UpdateProduct, db: Db_session, admin_user: Admin_user):
    updated_product = await get_updated_product(product_id, product, db)
    
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return updated_product

@router.delete("/{product_id}", tags=["Products"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id : int, db: Db_session, admin_user: Admin_user):
    deleted_product = await get_deleted_product(product_id, db)
    
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    return None