from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from src.schemas.users import ReadUser, CreateUser, UpdateUser, Token, ReadAllUsers, RefreshTokenRequest, UserRoleCurrent
from src.models.users import User as UserModel

from src.data_base.dependencies import Db_session

from src.auth.dependencies import get_current_user, require_role, get_current_active_user
from src.services.authentication.service import get_login_for_access_token, get_refresh_access_token
from src.services.users.service import updated_new_role, get_user_by_id, get_all_users, get_user_me, get_create_user, get_updated_user, get_deleted_user

router = APIRouter(prefix = "/users")

# Annotated dependency for requiring an admin user role
Admin_user = Annotated[UserModel, Depends(require_role("admin"))]

@router.get("/", tags = ["Users"], response_model=list[ReadAllUsers])
async def read_all_users(
    db: Db_session,
    admin_user: Admin_user,
    limit: int=20, 
    offset: int=0
):
    """
    Retrieve a list of all users with pagination.
    Only accessible by admin users.
    """
    users = await get_all_users(db, limit=limit, offset=offset)
    
    if users is not None:
        return users
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Users not found")

@router.get("/me", tags = ["Users"], response_model=ReadUser)
async def read_users_me(
    current_user: Annotated[UserModel, Depends(get_current_active_user)], 
    db: Db_session
): 
    """
    Retrieve the currently authenticated user's information.
    """
    user = await get_user_me(db,current_user)
    
    if user is not None:
        return  user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
@router.get("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def read_user(user_id : int, db: Db_session, admin_user: Admin_user):
    """
    Retrieve a user by their ID.
    Only accessible by admin users.
    """
    user = await get_user_by_id(db, user_id)
    
    if user is not None:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.post("/", tags = ["Users"], response_model=ReadUser)
async def create_user(user : CreateUser, db: Db_session):
    """
    Create a new user.
    Returns the created user or raises an error if the username already exists.
    """
    try:
        user_model = await get_create_user(user, db)
        return user_model
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"User with usernmae '{user.username}' already exists")

@router.patch("/admin/users/{username}/role", tags = ["Role"], response_model=ReadUser)
async def new_role_user(username: str, role: UserRoleCurrent, admin_user: Admin_user, db: Db_session):
    """
    Update the role of a user by username.
    Only accessible by admin users.
    """
    new_user_role = await updated_new_role(username, role.role, db)
    
    if new_user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'User with username {username} not found'
        )
    
    return new_user_role
    
@router.patch("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def update_user(user_id : int, user : UpdateUser, db: Db_session , admin_user: Admin_user):
    """
    Update a user's information by their ID.
    Only accessible by admin users.
    """
    updated_user = await get_updated_user(user_id, user, db)
    
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {user_id} not updated"
        )
    
    return updated_user

@router.delete("/{user_id}", tags = ["Users"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id : int, 
    db: Db_session, 
    admin_user: Admin_user
):
    """
    Delete a user by their ID.
    Only accessible by admin users.
    """
    deleted_user = await get_deleted_user(user_id, db)
    
    if deleted_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {user_id} not found"
        )
    
    return None
    
@router.post("/token", tags = ["Token"], response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Db_session
):
    """
    Authenticate user and return an access token.
    """
    token = await get_login_for_access_token(form_data, db)
    
    return token
    

@router.post("/token/refresh", tags = ["Token"], response_model=Token)
async def refresh_access_token(
    request: RefreshTokenRequest, 
    db: Db_session
):
    """
    Refresh the access token using a valid refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = await get_refresh_access_token(request, db, credentials_exception)
    
    return token
    

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    db: Db_session,
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Logout the current user by invalidating their refresh token.
    """
    current_user.hashed_refresh_token = None
    await db.commit()
    
    return {'message':'Logout success'}