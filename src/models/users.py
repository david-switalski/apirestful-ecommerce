from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, func
from src.data_base.base_class import Base
from datetime import datetime

class User(Base):
    id = Column(BigInteger,primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(512), nullable=False)
    available = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=datetime.utcnow, index=True)