import enum
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.data_base.base_class import Base
from src.models.orders import Order


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, index=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role_enum", create_type=True),
        nullable=False,
        default=UserRole.user,
    )
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    hashed_refresh_token: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete, delete-orphan"
    )
