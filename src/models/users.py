from sqlalchemy import Column, String, BigInteger, Boolean
from src.data_base.base_class import Base

class User(Base):
    id = Column(BigInteger,primary_key=True, index=True, autoincrement=True)
    fullname = Column(String(255), unique=True, index=True, nullable=False)
    available = Column(Boolean, default=True)