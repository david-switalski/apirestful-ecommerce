from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from src.schemas.users import ReadUser, CreateUser, UpdateUser, Token, ReadAllUsers, RefreshTokenRequest, UserRoleCurrent

from src.auth.dependencies import Current_user, Admin_user, Auth_user

from src.users.dependencies import get_user_service, get_authentication_service
from src.services.users.service import UserService
from src.services.authentication.service import AuthenticationService

router = APIRouter(prefix="/users")

@router.get("/", tags=["Users"], response_model=list[ReadAllUsers])
async def read_all_users(
    admin_user: Admin_user,
    limit: int = 20, 
    offset: int = 0,
    service: UserService = Depends(get_user_service)
):
    users = await service.get_all_users(limit=limit, offset=offset)
    return users

@router.get("/me", tags=["Users"], response_model=ReadUser)
async def read_users_me(current_user: Current_user, service: UserService = Depends(get_user_service)): 
    user = await service.get_user_me(current_user)
    return user
    
@router.get("/{user_id}", tags=["Users"], response_model=ReadUser)
async def read_user(user_id: int, admin_user: Admin_user, service: UserService = Depends(get_user_service)):
    user = await service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/", tags=["Users"], response_model=ReadUser, status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUser, service: UserService = Depends(get_user_service)):
    new_user = await service.create_user(user)
    return new_user

@router.patch("/admin/users/{username}/role", tags=["Role"], response_model=ReadUser)
async def new_role_user(
    username: str, 
    role: UserRoleCurrent, 
    admin_user: Admin_user, 
    service: UserService = Depends(get_user_service)
):
    updated_user = await service.update_user_role(username, role.role)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with username {username} not found')
    return updated_user
    
@router.patch("/{user_id}", tags=["Users"], response_model=ReadUser)
async def update_user(
    user_id: int, 
    user: UpdateUser, 
    admin_user: Admin_user,
    service: UserService = Depends(get_user_service)
):
    updated_user = await service.update_user(user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    return updated_user

@router.delete("/{user_id}", tags=["Users"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin_user: Admin_user, service: UserService = Depends(get_user_service)):
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    return None
    
@router.post("/token", tags=["Token"], response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthenticationService = Depends(get_authentication_service)
):
    token = await auth_service.get_login_for_access_token(form_data)
    return token
    
@router.post("/token/refresh", tags=["Token"], response_model=Token)
async def refresh_access_token(
    request: RefreshTokenRequest, 
    auth_service: AuthenticationService = Depends(get_authentication_service)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = await auth_service.refresh_access_token(request)
    return token
    
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: Current_user, auth_service: Auth_user):
    await auth_service.logout(current_user)
    return {'message': 'Logout success'}