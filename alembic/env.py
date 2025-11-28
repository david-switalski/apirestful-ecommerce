import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context
from src.data_base.base_class import Base
from src.models.orders import Order  # flake8: noqa: F401
from src.models.orders import OrderItem  # flake8: noqa: F401
from src.models.products import Product  # flake8: noqa: F401
from src.models.users import User  # flake8: noqa: F401


load_dotenv()


config = context.config

if config.get_main_option("sqlalchemy.url") is None:
    alembic_database_url = os.environ.get("DATABASE_URL_ALEMBIC")
    if not alembic_database_url:
        alembic_database_url = os.environ.get("DATABASE_URL")

    if alembic_database_url is None:
        raise ValueError("The database URL is not configured.")

    config.set_main_option("sqlalchemy.url", alembic_database_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():

    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            url=config.get_main_option("sqlalchemy.url"),
        )
    )

    async with connectable.connect() as connection:

        await connection.run_sync(do_run_migrations)


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
