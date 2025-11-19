from src.schemas.products import ReadProduct, CreateProduct, UpdateProduct, ReadAllProducts

from fastapi import APIRouter, Depends, HTTPException, status

from src.products.dependencies import get_product_service
from src.services.products.service import ProductService
from src.auth.dependencies import Admin_user

router = APIRouter(prefix = "/products")
 
@router.get("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def read_product(
    product_id: int,
    service: ProductService = Depends(get_product_service) 
):
    product = await service.get_product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.get("/", tags=["Products"], response_model=list[ReadAllProducts])
async def read_all_products(
    limit: int=20, 
    offset: int=0,
    service: ProductService = Depends(get_product_service)
):
    """
    Retrieve a list of all products with pagination.

    Args:
        db (Db_session): Database session dependency.
        limit (int): Maximum number of products to return. Defaults to 20.
        offset (int): Number of products to skip. Defaults to 0.

    Returns:
        list[ReadAllProducts]: A list of products.
    """
    products = await service.get_all_products(limit=limit,offset=offset)
    
    return products

@router.post("/create_product", tags=["Products"], response_model=ReadProduct, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: CreateProduct,
    admin_user: Admin_user,
    service: ProductService = Depends(get_product_service)
):
    created_product = await service.create_product(product)
    return created_product
    
@router.patch("/{product_id}", tags=["Products"], response_model=ReadProduct)
async def update_product(
    product_id : int, 
    product : UpdateProduct, 
    admin_user: Admin_user,
    service: ProductService = Depends(get_product_service)
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
    updated_product = await service.update_product(product_id, product)
    
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return updated_product

@router.delete("/{product_id}", tags=["Products"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id : int,  
    admin_user: Admin_user,
    service: ProductService = Depends(get_product_service)
):
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
    deleted_product = await service.delete_product(product_id)
    
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return None