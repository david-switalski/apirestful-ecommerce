from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, func, Enum
from sqlalchemy.orm import relationship
from src.data_base.base_class import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    
class User(Base):
    id = Column(BigInteger,primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole, name='user_role_enum'), nullable=False, default=UserRole.user)
    hashed_password = Column(String(512), nullable=False)
    hashed_refresh_token = Column(String(512), nullable=True)
    available = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=datetime.utcnow, index=True)
    
    orders = relationship("Order", back_populates="user",  cascade="all, delete, delete-orphan")