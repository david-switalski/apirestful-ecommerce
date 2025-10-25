from src.cache.dependencies import Redis_session

from src.data_base.dependencies import Db_session
from src.schemas.products import ReadProduct, CreateProduct, UpdateProduct, ReadAllProducts

from fastapi import APIRouter, HTTPException, status

from src.services.products.service import get_product_by_id, get_all_products, get_created_product, get_deleted_product, get_updated_product
from src.routers.users import Admin_user

router = APIRouter(prefix = "/products")
 
@router.get("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def read_product(db: Db_session, redis: Redis_session, product_id : int):
    """
    Retrieve a single product by its ID, utilizing a cache-aside strategy.

    Args:
        db (Db_session): Database session dependency.
        redis (Redis_session): Redis client dependency for caching.
        product_id (int): ID of the product to retrieve.

    Returns:
        ReadProduct: The product data if found.

    Raises:
        HTTPException: If the product is not found (404).
    """
    product = await get_product_by_id(db, redis, product_id )
    
    if product is not None:
        return  product
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

@router.get("/", tags=["Products"], response_model=list[ReadAllProducts])
async def read_all_products(db: Db_session, limit: int=20, offset: int=0):
    """
    Retrieve a list of all products with pagination.

    Args:
        db (Db_session): Database session dependency.
        limit (int): Maximum number of products to return. Defaults to 20.
        offset (int): Number of products to skip. Defaults to 0.

    Returns:
        list[ReadAllProducts]: A list of products.
    """
    products = await get_all_products(db, limit=limit, offset=offset)
    
    return products

@router.post("/create_product", tags=["Products"], response_model=ReadProduct, status_code=status.HTTP_201_CREATED)
async def create_product(product: CreateProduct, db: Db_session, admin_user: Admin_user):
    """
    Create a new product. Only accessible by admin users.

    Args:
        product (CreateProduct): Product data to create.
        db (Db_session): Database session dependency.
        admin_user (Admin_user): Admin user dependency.

    Returns:
        ReadProduct: The created product data.

    Raises:
        HTTPException:
            - status 409 (Conflict): If a product with the same name already exists.
            - status 400 (Bad Request): If a required field is missing.
    """
    created_product = await get_created_product(product, db)
    
    return created_product
    
    
    
@router.patch("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def update_product(
    product_id : int, 
    product : UpdateProduct, 
    db: Db_session, 
    redis: Redis_session, 
    admin_user: Admin_user
):
    """
    Update an existing product by its ID and invalidate its cache. Only accessible by admin users.


    Args:
        product_id (int): ID of the product to update.
        product (UpdateProduct): Updated product data.
        db (Db_session): Database session dependency.
        redis (Redis_session): Redis client dependency for cache invalidation.
        admin_user (Admin_user): Admin user dependency.

    Returns:
        ReadProduct: The updated product data.

    Raises:
        HTTPException: If the product is not found, returns 404.
    """
    updated_product = await get_updated_product(product_id,redis, product, db )
    
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return updated_product

@router.delete("/{product_id}", tags=["Products"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id : int, db: Db_session, redis: Redis_session, admin_user: Admin_user):
    """
    Delete a product by its ID and remove it from the cache. Only accessible by admin users.

    Args:
        product_id (int): ID of the product to delete.
        db (Db_session): Database session dependency.
        redis (Redis_session): Redis client dependency for cache invalidation.
        admin_user (Admin_user): Admin user dependency.

    Returns:
        None

    Raises:
        HTTPException: If the product is not found, returns 404.
    """
    deleted_product = await get_deleted_product(product_id, db, redis)
    
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return None