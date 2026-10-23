"""Integration suite: runs against the real PostgreSQL test database, never skipped.

TEST_DATABASE_URL is mandatory. Before any destructive step (migrate, downgrade, truncate) the target
must be the isolated test cluster: database name ending in `_test`, on 127.0.0.1:54329.
"""

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text

from app.domain.analysis import MarketAnalysis
from app.domain.run import AnalysisRun
from app.persistence.config import (
    create_db_engine,
    create_session_factory,
    load_test_database_url,
)
from app.persistence.errors import PersistenceConfigurationError
from app.persistence.models import AnalysisRunRow
from app.persistence.repository import AnalysisRunRepository
from tests.unit.conftest import make  # noqa: F401  (shared payload builders)

EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 54329
BACKEND_DIR = Path(__file__).resolve().parents[2]
TABLE = AnalysisRunRow.__table__


@pytest.fixture(scope="session")
def database_url():
    try:
        url = load_test_database_url()
    except PersistenceConfigurationError as exc:
        pytest.fail(f"integration tests need a valid TEST_DATABASE_URL: {exc}", pytrace=False)
    if (url.host, url.port) != (EXPECTED_HOST, EXPECTED_PORT):
        pytest.fail(
            f"integration tests only run against {EXPECTED_HOST}:{EXPECTED_PORT}", pytrace=False
        )
    return url


@pytest.fixture(scope="session")
def engine(database_url):
    engine = create_db_engine(database_url)
    with engine.connect() as connection:
        database, port, address, superuser = connection.execute(
            text(
                "select current_database(), inet_server_port(), host(inet_server_addr()),"
                " (select rolsuper from pg_roles where rolname = current_user)"
            )
        ).one()
    # The server's own view of where we connected, independent of anything written in the URL.
    if (
        not database.endswith("_test")
        or port != EXPECTED_PORT
        or address != EXPECTED_HOST
        or superuser
    ):
        engine.dispose()
        pytest.fail("connected server is not the isolated test database", pytrace=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def alembic_config(database_url):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = database_url
    config.attributes["configure_logging"] = False
    config.attributes["require_test_database"] = True
    return config


@pytest.fixture(scope="session")
def migrated(engine, alembic_config):
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    return engine


@pytest.fixture
def db(migrated):
    """Migrated engine with an empty analysis_runs table."""
    with migrated.begin() as connection:
        connection.execute(text("TRUNCATE analysis_runs"))
    return migrated


@pytest.fixture
def session_factory(db):
    return create_session_factory(db)


@pytest.fixture
def repo(session_factory):
    return AnalysisRunRepository(session_factory)


def raw_row(engine, analysis_id):
    with engine.connect() as connection:
        row = connection.execute(select(TABLE).where(TABLE.c.analysis_id == analysis_id)).mappings().one()
    return dict(row)


def new_pending(make, *, analysis_id=None, created="2026-09-18T14:30:00Z", mode="fixture") -> AnalysisRun:
    payload = make.run("pending")
    payload["analysis_id"] = str(analysis_id or uuid.uuid4())
    payload["created_at_utc"] = created
    payload["request"]["data_mode"] = mode
    return AnalysisRun.model_validate(payload)


def new_analysis(make, analysis_id, *, mode="fixture") -> MarketAnalysis:
    payload = make.analysis()
    payload["analysis_id"] = str(analysis_id)
    payload["market_snapshot"]["data_source"]["mode"] = mode
    payload["data_sources"][0]["mode"] = mode
    return MarketAnalysis.model_validate(payload)
