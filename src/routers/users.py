from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.schemas.users import ReadUser, CreateUser, UpdateUser, Token, ReadAllUsers, RefreshTokenRequest, UserRoleCurrent
from src.models.users import User as UserModel

from src.data_base.dependencies import Db_session

from src.auth.dependencies import get_current_user, Current_user, Admin_user
from src.services.authentication.service import get_login_for_access_token, get_refresh_access_token
from src.services.users.service import updated_new_role, get_user_by_id, get_all_users, get_user_me, get_create_user, get_updated_user, get_delete_user

router = APIRouter(prefix = "/users")

@router.get("/", tags = ["Users"], response_model=list[ReadAllUsers])
async def read_all_users(
    db: Db_session,
    admin_user: Admin_user,
    limit: int=20, 
    offset: int=0   
):
    """
    Retrieve a list of all users with pagination. Only accessible by admin users.

    Args:
        db (Db_session): Database session dependency.
        admin_user (Admin_user): Admin user dependency to protect the endpoint.
        limit (int): Maximum number of users to return.
        offset (int): Number of users to skip for pagination.

    Returns:
        list[ReadAllUsers]: A list of users with basic information.
    """
    users = await get_all_users(db, limit=limit, offset=offset)

    return users

@router.get("/me", tags = ["Users"], response_model=ReadUser)
async def read_users_me(
    current_user: Current_user, 
    db: Db_session
): 
    """
    Retrieve the profile information of the currently authenticated user.

    Args:
        current_user (Current_user): The authenticated user dependency.
        db (Db_session): Database session dependency.

    Returns:
        ReadUser: The detailed profile of the current user.
    """
    user = await get_user_me(db,current_user)
    
    if user is not None:
        return  user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
@router.get("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def read_user(user_id : int, db: Db_session, admin_user: Admin_user):
    """
    Retrieve a single user by their ID. Only accessible by admin users.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (Db_session): Database session dependency.
        admin_user (Admin_user): Admin user dependency.

    Returns:
        ReadUser: The detailed information of the specified user.

    Raises:
        HTTPException: 404 (Not Found) if the user does not exist.
    """
    user = await get_user_by_id(db, user_id)
    
    if user is not None:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.post("/", tags = ["Users"], response_model=ReadUser,status_code=status.HTTP_201_CREATED)
async def create_user(user : CreateUser, db: Db_session):
    """
    Create a new user. This is a public endpoint for registration.

    Args:
        user (CreateUser): The user data for registration.
        db (Db_session): Database session dependency.

    Returns:
        ReadUser: The newly created user's information.

    Raises:
        HTTPException: 409 (Conflict) if the username already exists.
    """
    new_user = await get_create_user(user, db)

    return new_user

@router.patch("/admin/users/{username}/role", tags = ["Role"], response_model=ReadUser)
async def new_role_user(username: str, role: UserRoleCurrent, admin_user: Admin_user, db: Db_session):
    """
    Update the role of a specific user. Only accessible by admin users.

    Prevents the demotion of the last remaining administrator.

    Args:
        username (str): The username of the user whose role is to be changed.
        role (UserRoleCurrent): The new role to assign.
        admin_user (Admin_user): Admin user dependency.
        db (Db_session): Database session dependency.

    Returns:
        ReadUser: The user's information with the updated role.

    Raises:
        HTTPException:
            - 404 (Not Found): If the user with the given username does not exist.
            - 409 (Conflict): If trying to demote the last admin.
    """
    new_user_role = await updated_new_role(username, role.role, db)
    if new_user_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with username {username} not found')
    
    return new_user_role
    
@router.patch("/{user_id}", tags = ["Users"], response_model=ReadUser)
async def update_user(user_id : int, user : UpdateUser, db: Db_session , admin_user: Admin_user):
    """
    Update a user's information by their ID. Only accessible by admin users.

    Allows for partial updates of username, password, or availability status.

    Args:
        user_id (int): The ID of the user to update.
        user (UpdateUser): The data to update. Fields are optional.
        db (Db_session): Database session dependency.
        admin_user (Admin_user): Admin user dependency.

    Returns:
        ReadUser: The updated user information.

    Raises:
        HTTPException: 404 (Not Found) if the user with the given ID does not exist.
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
    Delete a user by their ID. Only accessible by admin users.

    Prevents the deletion of the last administrator or users with existing orders.

    Args:
        user_id (int): The ID of the user to delete.
        db (Db_session): Database session dependency.
        admin_user (Admin_user): Admin user dependency.

    Raises:
        HTTPException:
            - 404 (Not Found): If the user does not exist.
            - 409 (Conflict): If the user is the last admin or has orders.
    """
    deleted_user = await get_delete_user(user_id, db)
    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    
    return None
    
@router.post("/token", tags = ["Token"], response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Db_session
):
    """
    Authenticate a user with username and password to get access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data with "username" and "password".
        db (Db_session): Database session dependency.

    Returns:
        Token: An object containing the access token, refresh token, and token type.

    Raises:
        HTTPException: 401 (Unauthorized) for invalid credentials.
    """
    token = await get_login_for_access_token(form_data, db)
    
    return token
    
@router.post("/token/refresh", tags = ["Token"], response_model=Token)
async def refresh_access_token(
    request: RefreshTokenRequest, 
    db: Db_session
):
    """
    Obtain a new access token using a valid refresh token.

    Args:
        request (RefreshTokenRequest): The request body containing the refresh token.
        db (Db_session): Database session dependency.

    Returns:
        Token: A new set of access and refresh tokens.

    Raises:
        HTTPException: 401 (Unauthorized) if the refresh token is invalid or expired.
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
    Log out the current user by invalidating their refresh token session.

    This is achieved by clearing the stored hashed refresh token in the database.

    Args:
        db (Db_session): Database session dependency.
        current_user (UserModel): The currently authenticated user.
    """
    current_user.hashed_refresh_token = None
    
    return {'message':'Logout success'}