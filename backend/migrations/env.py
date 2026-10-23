import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

import app.persistence.models  # noqa: F401  (registers the tables on Base.metadata)
from app.persistence.base import Base
from app.persistence.config import database_url_from_env, require_test_database
from app.persistence.errors import PersistenceConfigurationError

config = context.config

# Programmatic callers (tests) pass the URL and may keep their own logging configuration.
if config.config_file_name is not None and config.attributes.get("configure_logging", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> URL:
    url = config.attributes.get("database_url")
    if url is None:
        # A test run must never fall back to the application database.
        if "PYTEST_CURRENT_TEST" in os.environ:
            raise PersistenceConfigurationError("tests must pass the database URL explicitly")
        url = database_url_from_env()
    if config.attributes.get("require_test_database"):
        require_test_database(url)
    return url


def run_migrations_offline() -> None:
    context.configure(
        dialect_name="postgresql",
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url())
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
