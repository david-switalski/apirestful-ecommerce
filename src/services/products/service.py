from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.models.products import Product as ProductModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.products import CreateProduct, UpdateProduct

from src.core.exceptions import ProductNameAlreadyExistsError, ProductInUseError

async def get_product_by_id(db: AsyncSession, product_id: int) -> ProductModel | None:
    """
    Retrieve a single product by its ID.

    Args:
        db (AsyncSession): The database session.
        product_id (int): The ID of the product to retrieve.

    Returns:
        ProductModel | None: The product instance if found, otherwise None.
    """
    product = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    return product.scalars().first()

async def get_all_products(db: AsyncSession, limit, offset) -> list[ProductModel]:
    """
    Retrieve all products with pagination.

    Args:
        db (AsyncSession): The database session.
        limit (int): Maximum number of products to return.
        offset (int): Number of products to skip.

    Returns:
        list[ProductModel]: List of product instances.
    """
    products = await db.execute(select(ProductModel).limit(limit).offset(offset))
    return products.scalars().all()

async def get_created_product(product: CreateProduct, db: AsyncSession) -> ProductModel:
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
    return created_product

async def get_updated_product(id: int, product: UpdateProduct, db: AsyncSession) -> ProductModel | None:
    """
    Update an existing product by its ID.

    Args:
        id (int): The ID of the product to update.
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

    return updated_product    

async def get_deleted_product(id: int, db: AsyncSession) -> ProductModel | None:
    """
    Delete a product by its ID.

    Args:
        id (int): The ID of the product to delete.
        db (AsyncSession): The database session.

    Returns:
        ProductModel | None: The deleted product instance if found, otherwise None.
        
    Raises:
        ProductInUseError: If the product is part of an existing order.
    """
    stmt = select(ProductModel).options(selectinload(ProductModel.order_items)).where(ProductModel.id == id)
    result = await db.execute(stmt)
    deleted_product = result.scalars().first()

    if deleted_product is None:
        return None

    if deleted_product.order_items:
        raise ProductInUseError(product_name=deleted_product.name)

    await db.delete(deleted_product)
    await db.flush()
    return deleted_product