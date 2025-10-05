from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.models.users import User as UserModel, UserRole

from src.schemas.users import CreateUser, UpdateUser
from src.services.authentication.service import get_password_hash, get_user
from src.core.exceptions import LastAdminError, UselessOperationError, UsernameAlreadyExistsError, UserHasOrdersError

async def get_user_by_id(db: AsyncSession, user_id: int) -> UserModel | None:
    """
    Retrieve a user by their unique ID.

    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        UserModel | None: The user object if found, otherwise None.
    """
    user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    
    return user.scalars().first()

async def get_all_users(db: AsyncSession, limit, offset) -> list[UserModel]:
    """
    Retrieve all users with pagination.

    Args:
        db (AsyncSession): The database session.
        limit (int): Maximum number of users to return.
        offset (int): Number of users to skip.

    Returns:
        Sequence[UserModel]: List of user objects.
    """
    users = await db.execute(select(UserModel).limit(limit).offset(offset))
     
    return users.scalars().all()

async def get_user_me(db: AsyncSession, current_user) -> UserModel:
    """
    Retrieve the current authenticated user.

    Args:
        db (AsyncSession): The database session.
        current_user (UserModel): The currently authenticated user.

    Returns:
        UserModel | None: The user object if found, otherwise None.
    """
    user = await db.execute(select(UserModel).where(UserModel.id == current_user.id))
    
    return user.scalars().first()

async def get_create_user(user: CreateUser, db: AsyncSession) -> UserModel:
    """
    Create a new user in the database.

    Args:
        user (CreateUser): The user creation schema.
        db (AsyncSession): The database session.

    Returns:
        UserModel: The newly created user object.
        
    Raises:
        UsernameAlreadyExistsError: If the username is already taken.
    """
    user_data = user.model_dump(exclude={'password'})
    plain_password = user.password.get_secret_value()
    hashed_pass = await get_password_hash(plain_password)
    
    model = UserModel(**user_data, hashed_password=hashed_pass)
    db.add(model)
    try:
        await db.flush()
    except IntegrityError:
        raise UsernameAlreadyExistsError(username=user.username)
    
    await db.refresh(model)
    return model

async def updated_new_role(username: str, role: UserRole, db: AsyncSession) -> UserModel:
    """
    Update the role of a user, ensuring at least one admin remains.

    Args:
        username (str): The username of the user to update.
        role (UserRole): The new role to assign.
        db (AsyncSession): The database session.

    Raises:
        UselessOperationError: If the user already has the specified role.
        LastAdminError: If attempting to demote the last admin.

    Returns:
        UserModel | None: The updated user object, or None if not found.
    """
    user_to_change = await get_user(username, db)
    if user_to_change is None:
        return None

    count_admins_user = await db.execute(select(func.count(UserModel.id)).where(UserModel.role == UserRole.admin))
    total_admins = count_admins_user.scalar_one()

    if user_to_change.role == role:
        raise UselessOperationError(username=username)

    if user_to_change.role == UserRole.admin and role == UserRole.user and total_admins <= 1:
        raise LastAdminError(username=username, action="demote")

    user_to_change.role = role
    await db.flush()
    await db.refresh(user_to_change)
    return user_to_change

async def get_updated_user(id: int, user: UpdateUser, db: AsyncSession) -> UserModel:
    """
    Update an existing user's information.

    Args:
        id (int): The ID of the user to update.
        user (UpdateUser): The update schema with new user data.
        db (AsyncSession): The database session.

    Returns:
        UserModel | None: The updated user object, or None if not found.
    """
    result = await db.execute(select(UserModel).where(UserModel.id == id))
    user_db = result.scalars().first()

    if user_db is not None:
        update_data = user.model_dump(exclude_unset=True)

        # Handle password update if provided
        if "password" in update_data:
            update_data["hashed_password"] = await get_password_hash(user.password.get_secret_value())
            del update_data["password"]

        for key, value in update_data.items():
            setattr(user_db, key, value)

        await db.flush()
        await db.refresh(user_db)

    return user_db

async def get_delete_user(id: int, db: AsyncSession) -> UserModel | None:
    """
    Delete a user by ID, ensuring at least one admin remains.

    Args:
        id (int): The ID of the user to delete.
        db (AsyncSession): The database session.

    Raises:
        LastAdminError: If attempting to delete the last admin.
        UserHasOrdersError: If the user has existing orders.

    Returns:
        UserModel | None: The deleted user object, or None if not found.
    """
    stmt = select(UserModel).options(selectinload(UserModel.orders)).where(UserModel.id == id)
    result = await db.execute(stmt)
    deleted_user = result.scalars().first()

    if deleted_user is None:
        return None

    if deleted_user.orders:
        raise UserHasOrdersError(username=deleted_user.username)

    count_admins_user = await db.execute(select(func.count(UserModel.id)).where(UserModel.role == UserRole.admin))
    total_admins = count_admins_user.scalar_one()

    if deleted_user.role == UserRole.admin and total_admins <= 1:
        raise LastAdminError(username=deleted_user.username, action="delete")

    await db.delete(deleted_user)
    await db.flush()
    return deleted_user