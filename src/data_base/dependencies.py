from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.data_base.session import get_db

Db_session = Annotated[AsyncSession, Depends(get_db)]

