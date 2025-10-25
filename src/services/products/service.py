from redis.asyncio import Redis

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.models.products import Product as ProductModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.products import CreateProduct, UpdateProduct, ReadProduct, ReadAllProducts

from src.core.exceptions import ProductNameAlreadyExistsError, ProductInUseError

async def get_product_by_id(db: AsyncSession, redis_client: Redis, product_id: int) -> ReadProduct | None:
    """
    Retrieve a single product by its ID using a cache-aside strategy.

    Args:
        db (AsyncSession): The database session.
        redis_client (Redis): The Redis client for caching.
        product_id (int): The ID of the product to retrieve.

    Returns:
        ReadProduct | None: A Pydantic schema of the product if found, otherwise None.
    """
    
    cache_key = f"product:{product_id}"

    cached_product = await redis_client.get(cache_key)

    if cached_product:
        # If found in cache, deserialize JSON and return Pydantic model
        return ReadProduct.model_validate_json(cached_product)

    # If not in cache, query the database
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product_from_db = result.scalars().first()


    if product_from_db:
        # If found in DB, validate with Pydantic and store in cache
        product_schema = ReadProduct.model_validate(product_from_db)
        
        await redis_client.set(
            name=cache_key,
            value=product_schema.model_dump_json(),
            ex=600 # Cache expires in 10 minutes
        )
        return product_schema
    
    return None

async def get_all_products(db: AsyncSession, limit, offset) -> list[ReadAllProducts]:
    """
    Retrieve all products with pagination.

    Args:
        db (AsyncSession): The database session.
        limit (int): Maximum number of products to return.
        offset (int): Number of products to skip.

    Returns:
        list[ProductModel]: List of product instances.
    """
    results = await db.execute(select(ProductModel).limit(limit).offset(offset))
    products_list = results.scalars().all()

    return [ReadAllProducts.model_validate(product) for product in products_list]
            
async def get_created_product(product: CreateProduct, db: AsyncSession) -> ReadProduct:
    """
    Create a new product in the database.

    Args:
        product (CreateProduct): The product data to create.
        db (AsyncSession): The database session.

    Returns:
        ProductModel: The newly created product instance.
        
    Raises:
        ProductNameAlreadyExistsError: If the product name is already in use.
    """
    created_product = ProductModel(**product.model_dump())
    db.add(created_product)
    try:
        await db.flush()  
    except IntegrityError:
        raise ProductNameAlreadyExistsError(name=product.name)
    
    await db.refresh(created_product)
    return ReadProduct.model_validate(created_product)

async def get_updated_product(id: int, redis_client: Redis, product: UpdateProduct, db: AsyncSession) -> ReadProduct | None:
    """
    Update an existing product by its ID and invalidate its cache entry.

    Args:
        id (int): The ID of the product to update
        redis_client (Redis): The Redis client for cache invalidation
        product (UpdateProduct): The updated product data.
        db (AsyncSession): The database session.

    Returns:
        ProductModel | None: The updated product instance if found, otherwise None.
    """
    result = await db.execute(select(ProductModel).where(ProductModel.id == id))
    updated_product = result.scalars().first()

    if updated_product is not None:
        update_data = product.model_dump(exclude_unset=True)
        # Update only the fields provided in the update_data
        for key, value in update_data.items():
            setattr(updated_product, key, value)
        await db.flush()
        await db.refresh(updated_product)
        
        # Invalidate the cache for this product
        cache_key = f"product:{id}"
        await redis_client.delete(cache_key)

    return ReadProduct.model_validate(updated_product) if updated_product else None 

async def get_deleted_product(id: int, db: AsyncSession, redis_client: Redis) -> ReadProduct | None:
    """
    Delete a product by its ID and remove its corresponding cache entry.

    Args:
        id (int): The ID of the product to delete.
        db (AsyncSession): The database session.
        redis_client (Redis): The Redis client for cache invalidation.

    Returns:
        ProductModel | None: The deleted product instance if found, otherwise None.
        
    Raises:
        ProductInUseError: If the product is part of an existing order.
    """
    stmt = select(ProductModel).options(selectinload(ProductModel.order_items)).where(ProductModel.id == id)
    result = await db.execute(stmt)
    product_to_delete = result.scalars().first()

    if product_to_delete is None:
        return None

    if product_to_delete.order_items:
        raise ProductInUseError(product_name=product_to_delete.name)

    deleted_product_schema = ReadProduct.model_validate(product_to_delete)

    cache_key = f"product:{id}"
    await redis_client.delete(cache_key)
    
    await db.delete(product_to_delete)
    await db.flush()
    
    return deleted_product_schema