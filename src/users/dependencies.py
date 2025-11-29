from fastapi import Depends

from src.data_base.dependencies import Db_session
from src.repositories.user_repository import UserRepository
from src.services.authentication.service import AuthenticationService
from src.services.users.service import UserService


def get_user_repository(db: Db_session) -> UserRepository:
    """
    Dependency provider for UserRepository.
    """
    return UserRepository(db)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """
    Dependency provider for UserService.
    """
    return UserService(repo)


def get_authentication_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthenticationService:
    """
    Dependency provider for AuthenticationService.
    """
    return AuthenticationService(user_service)
