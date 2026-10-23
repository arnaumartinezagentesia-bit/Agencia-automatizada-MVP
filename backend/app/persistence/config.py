import os
from collections.abc import Mapping

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.errors import PersistenceConfigurationError

DATABASE_URL_ENV = "DATABASE_URL"
TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"
TEST_DATABASE_SUFFIX = "_test"
_DRIVER = "postgresql+psycopg"


def parse_database_url(raw: str | None, *, env_var: str) -> URL:
    """Parse and check a PostgreSQL URL. Errors name the variable, never echo the value."""
    if raw is None or not raw.strip():
        raise PersistenceConfigurationError(f"{env_var} is not set")
    try:
        url = make_url(raw.strip())
    except ArgumentError:
        url = None
    if url is None:
        raise PersistenceConfigurationError(f"{env_var} is not a valid database URL")
    if url.drivername != _DRIVER:
        raise PersistenceConfigurationError(f"{env_var} must use the {_DRIVER} driver")
    if not url.database:
        raise PersistenceConfigurationError(f"{env_var} must name a database")
    return url


def database_url_from_env(environ: Mapping[str, str] | None = None) -> URL:
    env = os.environ if environ is None else environ
    return parse_database_url(env.get(DATABASE_URL_ENV), env_var=DATABASE_URL_ENV)


def require_test_database(url: URL) -> URL:
    """Refuse any target whose database name does not end in `_test`.

    Query parameters are refused too: libpq honours `host=`, `hostaddr=`, `service=` and similar
    there, which would silently redirect the connection away from the host written in the URL.
    """
    if url.query:
        raise PersistenceConfigurationError("the test database URL must not carry query parameters")
    if not (url.database or "").endswith(TEST_DATABASE_SUFFIX):
        raise PersistenceConfigurationError(
            f"refusing to use a database whose name does not end in {TEST_DATABASE_SUFFIX!r}"
        )
    return url


def load_test_database_url(environ: Mapping[str, str] | None = None) -> URL:
    env = os.environ if environ is None else environ
    url = parse_database_url(env.get(TEST_DATABASE_URL_ENV), env_var=TEST_DATABASE_URL_ENV)
    return require_test_database(url)


def create_db_engine(url: URL) -> Engine:
    # Session time zone is pinned to UTC so timestamptz values never depend on server settings.
    return create_engine(url, pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"})


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
