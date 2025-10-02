from pydantic import BaseModel, ConfigDict, Field
from src.models.orders import OrderState
from datetime import datetime
from decimal import Decimal

# --- ORDER ITEM SCHEMA ---

class OrderItemBase(BaseModel):
    product_id: int = Field(..., gt=0, description="The ID of the product.")
    quantity: int = Field(..., gt=0, description="The quantity of the product.")

class OrderItemCreate(OrderItemBase):
    pass

class ReadOrderItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    product_id: int
    quantity: int
    unit_price: Decimal

# --- ORDER SCHEMA ---

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]

class ReadOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    user_id: int
    total_price: Decimal
    state: OrderState
    order_date: datetime
    items: list[ReadOrderItem]
