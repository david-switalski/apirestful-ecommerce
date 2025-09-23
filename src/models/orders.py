from sqlalchemy import Column, DateTime, BigInteger, ForeignKey, func, Integer, Enum, Numeric
from sqlalchemy.orm import relationship
from src.data_base.base_class import Base
from datetime import datetime
import enum

class OrderState(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class Order(Base):
    order_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    total_price = Column(Numeric, nullable=False)
    state = Column(Enum(OrderState, name='order_state_enum'), nullable=False, default=OrderState.pending)
    
    order_date = Column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)
    
    items = relationship("OrderItem", back_populates="order",  cascade="all, delete, delete-orphan")
    user = relationship("User", back_populates="orders")
    

class OrderItem(Base):
    order_item_id = Column(BigInteger, primary_key=True, index=True)
    order_id = Column(BigInteger, ForeignKey("order.order_id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("product.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
