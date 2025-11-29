from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import relationship

from src.data_base.base_class import Base


class Product(Base):
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    price = Column(Numeric, nullable=False)
    stock = Column(Integer, nullable=False)
    category = Column(String(255), index=True, nullable=False)
    available = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), default=datetime.utcnow
    )

    order_items = relationship("OrderItem", back_populates="product")
