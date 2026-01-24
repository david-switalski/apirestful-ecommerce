import enum
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    hashed_refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete, delete-orphan"
    )
