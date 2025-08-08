import jwt
from jwt import InvalidTokenError
import uuid

from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status

from src.schemas.users import Token, RefreshTokenRequest
from src.data_base.dependencies import Db_session
from src.core.config import settings
from sqlalchemy import select
from src.models.users import User as UserModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user(username: str, db: Db_session):
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    
    user = result.scalars().first()
    
    return user

async def get_password_hash(password):
    return pwd_context.hash(password)

async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
    
async def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.ISSUER,
        "aud": settings.AUDIENCE,
        "jti": str(uuid.uuid4())
        }
    ) 
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.ISSUER,
        "aud": settings.AUDIENCE,
        "jti": str(uuid.uuid4())
        }
    ) 
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def authenticate_user(username: str, password: str, db: Db_session):
    user = await get_user(username, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    if await verify_password(password, user.hashed_password):
        return user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


async def get_login_for_access_token(form_data:OAuth2PasswordRequestForm, db:Db_session):
    
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_refresh_token = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = await create_access_token(
        data= {"sub": user.username, "type": "access"},
        expires_delta=access_token_expire
    )
    
    refresh_token = await create_refresh_token(
        data= {"sub": user.username, "type": "refresh"},
        expires_delta=access_refresh_token
    )
    
    user.hashed_refresh_token = await get_password_hash(refresh_token)
    await db.commit()
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
    
async def get_refresh_access_token(request: RefreshTokenRequest, db: Db_session, credentials_exception: HTTPException):
    try:
       
        payload = jwt.decode(
            request.refresh_token, 
            settings.SECRET_KEY, 
            audience=settings.AUDIENCE,
            issuer=settings.ISSUER,
            algorithms=[settings.ALGORITHM])
        

        if payload.get("type") != "refresh":
            raise credentials_exception
            
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception


        user = await get_user(username, db)
        if user is None or user.hashed_refresh_token is None:
            raise credentials_exception

        username_for_token = user.username
        
        is_valid_refresh_token = await verify_password(request.refresh_token, user.hashed_refresh_token)
        if not is_valid_refresh_token:
            raise credentials_exception

        new_refresh_token = await create_refresh_token(data={"sub": username_for_token, "type": "refresh"})
        user.hashed_refresh_token = await get_password_hash(new_refresh_token)
        await db.commit()

        new_access_token = await create_access_token(data={"sub": username_for_token, "type": "access"})

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token, 
            token_type="bearer"
        )

    except InvalidTokenError:
        raise credentials_exception
