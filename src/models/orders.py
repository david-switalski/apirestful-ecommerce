import enum
from datetime import datetime
from decimal import Decimal
from typing import List
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.data_base.base_class import Base

if TYPE_CHECKING:
    from src.models.products import Product
    from src.models.users import User


class OrderState(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(Base):
    order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    state: Mapped[OrderState] = mapped_column(
        Enum(OrderState, name="order_state_enum"),
        nullable=False,
        default=OrderState.pending,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow
    )

    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete, delete-orphan"
    )
    user: Mapped["User"] = relationship(back_populates="orders")


class OrderItem(Base):
    order_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.order_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
