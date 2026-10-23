import logging

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from app.persistence.config import (
    DATABASE_URL_ENV,
    TEST_DATABASE_URL_ENV,
    create_db_engine,
    database_url_from_env,
    load_test_database_url,
    parse_database_url,
    require_test_database,
)
from app.persistence.errors import PersistenceConfigurationError, PersistenceError
from app.persistence.repository import AnalysisRunRepository

SECRET = "hunter2-very-secret"
GOOD = "postgresql+psycopg://runner@127.0.0.1:54329/agencia_automatizada_test"


def test_missing_url_is_a_clear_error_naming_the_variable():
    with pytest.raises(PersistenceConfigurationError, match=DATABASE_URL_ENV):
        database_url_from_env({})


def test_blank_url_is_treated_as_missing():
    with pytest.raises(PersistenceConfigurationError, match="not set"):
        parse_database_url("   ", env_var=DATABASE_URL_ENV)


@pytest.mark.parametrize(
    "raw",
    [
        f"not a url {SECRET}",
        f"mysql://user:{SECRET}@host/db",
        f"postgresql://user:{SECRET}@host/db",  # default driver is not the one we ship
        f"postgresql+psycopg://user:{SECRET}@host",  # no database name
    ],
)
def test_invalid_urls_are_rejected_without_echoing_secrets(raw):
    with pytest.raises(PersistenceConfigurationError) as info:
        parse_database_url(raw, env_var=DATABASE_URL_ENV)

    assert SECRET not in str(info.value)
    assert SECRET not in repr(info.value)


def test_valid_url_is_parsed():
    url = parse_database_url(GOOD, env_var=DATABASE_URL_ENV)

    assert (url.host, url.port, url.database, url.username) == (
        "127.0.0.1",
        54329,
        "agencia_automatizada_test",
        "runner",
    )


def test_test_url_is_required():
    with pytest.raises(PersistenceConfigurationError, match=TEST_DATABASE_URL_ENV):
        load_test_database_url({})


@pytest.mark.parametrize("database", ["agencia_automatizada", "agencia_test_old", "testing", "prod"])
def test_databases_not_ending_in_test_are_refused(database):
    environ = {TEST_DATABASE_URL_ENV: f"postgresql+psycopg://u:{SECRET}@127.0.0.1:54329/{database}"}

    with pytest.raises(PersistenceConfigurationError) as info:
        load_test_database_url(environ)

    assert "_test" in str(info.value)
    assert SECRET not in str(info.value)
    assert database not in str(info.value)


@pytest.mark.parametrize(
    "query", ["?host=other-server", "?hostaddr=10.0.0.9", "?service=prod", "?options=-c%20x=1"]
)
def test_test_urls_with_query_parameters_are_refused(query):
    raw = f"postgresql+psycopg://u@127.0.0.1:54329/agencia_automatizada_test{query}"

    with pytest.raises(PersistenceConfigurationError, match="query parameters"):
        load_test_database_url({TEST_DATABASE_URL_ENV: raw})


def test_invalid_url_error_has_no_context_holding_the_value():
    with pytest.raises(PersistenceConfigurationError) as info:
        parse_database_url(f"not a url {SECRET}", env_var=DATABASE_URL_ENV)

    assert info.value.__context__ is None and info.value.__cause__ is None


def test_database_errors_are_logged_without_message_or_payload(caplog):
    secret_error = OperationalError("SELECT 1", {"p": SECRET}, Exception(f"password={SECRET}"))

    class BrokenSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def begin(self):
            raise secret_error

    repo = AnalysisRunRepository(sessionmaker())
    repo._session_factory = lambda: BrokenSession()  # noqa: SLF001

    with caplog.at_level(logging.WARNING, logger="app.persistence.repository"):
        with pytest.raises(PersistenceError):
            repo._run(None, lambda s: None)  # noqa: SLF001

    assert "OperationalError" in caplog.text
    assert SECRET not in caplog.text


def test_test_database_is_accepted():
    url = load_test_database_url({TEST_DATABASE_URL_ENV: GOOD})

    assert require_test_database(url) is url


def test_application_and_test_settings_are_separate_variables():
    environ = {TEST_DATABASE_URL_ENV: GOOD}

    with pytest.raises(PersistenceConfigurationError):
        database_url_from_env(environ)


def test_engine_creation_does_not_connect_or_log_credentials(caplog):
    url = parse_database_url(
        f"postgresql+psycopg://u:{SECRET}@127.0.0.1:1/agencia_x_test", env_var=DATABASE_URL_ENV
    )

    with caplog.at_level(logging.DEBUG):
        engine = create_db_engine(url)
    engine.dispose()

    assert SECRET not in caplog.text


def test_database_errors_are_reported_without_driver_details():
    secret_error = OperationalError("SELECT 1", {}, Exception(f"password={SECRET} host=10.0.0.9"))

    class BrokenSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def begin(self):
            raise secret_error

    repo = AnalysisRunRepository(sessionmaker())
    repo._session_factory = lambda: BrokenSession()  # noqa: SLF001

    with pytest.raises(PersistenceError) as info:
        repo._run(None, lambda s: None)  # noqa: SLF001

    assert SECRET not in str(info.value)
    assert "10.0.0.9" not in str(info.value)
    assert info.value.__cause__ is None
    assert info.value.__context__ is None



class _WorkingSession:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def begin(self):
        return self


@pytest.mark.parametrize(
    "failure",
    [
        OperationalError("INSERT ...", {"analysis": SECRET}, Exception(f"password={SECRET} host=10.0.0.9")),
        IntegrityError("INSERT ...", {"analysis": SECRET}, Exception(f"password={SECRET}")),
    ],
)
def test_errors_raised_by_the_work_leave_no_context_or_cause(failure):
    # The error comes from inside the transaction body, the path that real queries take.
    repo = AnalysisRunRepository(sessionmaker())
    repo._session_factory = lambda: _WorkingSession()  # noqa: SLF001

    def work(session):
        raise failure

    with pytest.raises(PersistenceError) as info:
        repo._run(None, work)  # noqa: SLF001

    assert info.value.__cause__ is None and info.value.__context__ is None
    assert SECRET not in str(info.value) and "10.0.0.9" not in str(info.value)


def test_errors_raised_by_the_work_on_a_caller_owned_session_leave_no_context():
    repo = AnalysisRunRepository(sessionmaker())

    def work(session):
        raise OperationalError("SELECT 1", {"p": SECRET}, Exception(SECRET))

    with pytest.raises(PersistenceError) as info:
        repo._run(object(), work)  # noqa: SLF001

    assert info.value.__context__ is None


def test_domain_errors_raised_by_the_work_pass_through_unchanged():
    repo = AnalysisRunRepository(sessionmaker())
    repo._session_factory = lambda: _WorkingSession()  # noqa: SLF001
    original = ValueError("domain problem")

    def work(session):
        raise original

    with pytest.raises(ValueError) as info:
        repo._run(None, work)  # noqa: SLF001

    assert info.value is original
