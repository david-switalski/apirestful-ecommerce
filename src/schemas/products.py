from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class Product(BaseModel):
    """
    Base schema for a product entity.

    Attributes:
        name (str): Name of the product.
        category (str): Category to which the product belongs.
        price (float): Price of the product.
        stock (int): Number of items in stock.
        description (str): Description of the product.
        available (bool): Availability status of the product. Defaults to True.
    """

    model_config = ConfigDict(extra="forbid")
    name: str
    category: str
    price: float
    stock: int
    description: str
    available: bool = True


class CreateProduct(Product):
    """
    Schema for creating a new product.
    Inherits all fields from Product.
    """

    pass


class UpdateProduct(BaseModel):
    """
    Schema for updating an existing product.
    All fields are optional to allow partial updates.

    Attributes:
        name (Optional[str]): Updated name of the product.
        category (Optional[str]): Updated category.
        price (Optional[float]): Updated price.
        stock (Optional[int]): Updated stock.
        description (Optional[str]): Updated description.
        available (Optional[bool]): Updated availability status.
    """

    name: str | None = None
    category: str | None = None
    price: float | None = None
    stock: int | None = None
    description: str | None = None
    available: bool | None = None


class ReadProduct(Product):
    """
    Schema for reading a product from the database.

    Attributes:
        id (int): Unique identifier of the product.
        created_at (Optional[datetime]): Timestamp when the product was created.
        updated_at (Optional[datetime]): Timestamp when the product was last updated.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: int
    created_at: datetime | None
    updated_at: datetime | None


class ReadAllProducts(BaseModel):
    """
    Schema for listing all products with limited fields.

    Attributes:
        id (int): Unique identifier of the product.
        name (str): Name of the product.
        price (float): Price of the product.
        description (str): Description of the product.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    description: str
