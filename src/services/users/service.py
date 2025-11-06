from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError

from src.models.users import User as UserModel, UserRole
from src.schemas.users import CreateUser, UpdateUser, ReadAllUsers, ReadUser
from src.services.authentication.service import get_password_hash
from src.repositories.user_repository import UserRepository
from src.core.exceptions import LastAdminError, UselessOperationError, UsernameAlreadyExistsError, UserHasOrdersError

class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    async def get_user_by_id(self, user_id: int) -> ReadUser | None:
        user_model = await self.repo.get_by_id(user_id)
        if user_model:
            return ReadUser.model_validate(user_model)
        return None

    async def get_all_users(self, limit: int, offset: int) -> list[ReadAllUsers]:
        user_models = await self.repo.get_all(limit, offset)
        return [ReadAllUsers.model_validate(user) for user in user_models]

    async def get_user_me(self, current_user: UserModel) -> ReadUser:
        user_model = await self.repo.get_by_id(current_user.id)
        return ReadUser.model_validate(user_model)

    async def create_user(self, user_data: CreateUser) -> ReadUser:
        if await self.repo.get_by_username(user_data.username):
            raise UsernameAlreadyExistsError(username=user_data.username)

        user_dict = user_data.model_dump(exclude={'password'})
        plain_password = user_data.password.get_secret_value()
        hashed_pass = await get_password_hash(plain_password)
        
        user_model = UserModel(**user_dict, hashed_password=hashed_pass)
        
        try:
            created_model = await self.repo.add(user_model)
        except IntegrityError as exc:
            if isinstance(exc.orig, UniqueViolationError):
                raise UsernameAlreadyExistsError(username=user_data.username)
            else:
                raise
        
        return ReadUser.model_validate(created_model)

    async def update_user_role(self, username: str, role: UserRole) -> ReadUser | None:
        user_to_change = await self.repo.get_by_username(username)
        if not user_to_change:
            return None

        if user_to_change.role == role:
            raise UselessOperationError(username=username)

        if user_to_change.role == UserRole.admin and role == UserRole.user:
            total_admins = await self.repo.count_admins()
            if total_admins <= 1:
                raise LastAdminError(username=username, action="demote")

        user_to_change.role = role
        updated_model = await self.repo.update(user_to_change)
        return ReadUser.model_validate(updated_model)

    async def update_user(self, user_id: int, user_data: UpdateUser) -> ReadUser | None:
        user_model = await self.repo.get_by_id(user_id)
        if not user_model:
            return None

        update_dict = user_data.model_dump(exclude_unset=True)
        if "password" in update_dict:
            update_dict["hashed_password"] = await get_password_hash(user_data.password.get_secret_value())
            del update_dict["password"]

        for key, value in update_dict.items():
            setattr(user_model, key, value)

        updated_model = await self.repo.update(user_model)
        return ReadUser.model_validate(updated_model)

    async def delete_user(self, user_id: int) -> bool:
        user_to_delete = await self.repo.get_by_id_with_orders(user_id)
        if not user_to_delete:
            return False

        if user_to_delete.orders:
            raise UserHasOrdersError(username=user_to_delete.username)
        
        if user_to_delete.role == UserRole.admin:
            total_admins = await self.repo.count_admins()
            if total_admins <= 1:
                raise LastAdminError(username=user_to_delete.username, action="delete")

        await self.repo.delete(user_to_delete)
        return True