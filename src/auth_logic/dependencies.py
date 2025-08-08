from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError

from src.models.users import User as UserModel
from src.schemas.users import TokenData
from src.core.config import settings
from src.data_base.dependencies import Db_session
from src.services.authentication.service import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
               
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db : Db_session
    ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "access":
            raise credentials_exception
        
        username = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)
        
    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    if not current_user.available:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return current_user



def require_role(required_role:str):
    async def role_checker(current_user: Annotated[UserModel, Depends(get_current_active_user)]):
        if current_user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Forbidden")
        
        return current_user
    
    return role_checker