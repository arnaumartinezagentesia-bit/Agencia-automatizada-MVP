import pytest
from alembic import command
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import CheckConstraint, inspect, text

from app.persistence.models import AnalysisRunRow


@pytest.fixture
def restore_head(migrated, alembic_config):
    """Whatever the test does to the schema, leave the shared database at head."""
    yield migrated
    command.upgrade(alembic_config, "head")


def _tables(engine):
    return set(inspect(engine).get_table_names())


def test_migration_history_is_linear_with_a_single_head(alembic_config):
    script = ScriptDirectory.from_config(alembic_config)

    assert len(script.get_heads()) == 1
    revisions = list(script.walk_revisions())
    assert all(not isinstance(r.down_revision, tuple) for r in revisions)  # no merges
    assert [r.down_revision for r in revisions].count(None) == 1  # one root


def test_upgrade_creates_the_expected_columns(migrated):
    columns = {c["name"]: c for c in inspect(migrated).get_columns("analysis_runs")}

    assert list(columns) == [
        "analysis_id",
        "request_id",
        "status",
        "symbol",
        "timeframe",
        "data_mode",
        "created_at_utc",
        "started_at_utc",
        "completed_at_utc",
        "failed_at_utc",
        "error",
        "analysis",
        "failure_snapshot",
    ]
    types = {name: c["type"].__class__.__name__ for name, c in columns.items()}
    assert types["analysis_id"] == types["request_id"] == "UUID"
    assert types["created_at_utc"] == "TIMESTAMP"
    assert columns["created_at_utc"]["type"].timezone is True
    assert {types[c] for c in ("error", "analysis", "failure_snapshot")} == {"JSONB"}
    required = {"analysis_id", "request_id", "status", "symbol", "timeframe", "data_mode", "created_at_utc"}
    assert {name for name, c in columns.items() if not c["nullable"]} == required


def test_only_the_justified_indexes_exist(migrated):
    with migrated.connect() as connection:
        definitions = dict(
            connection.execute(
                text("select indexname, indexdef from pg_indexes where tablename = 'analysis_runs'")
            ).all()
        )

    assert set(definitions) == {"pk_analysis_runs", "ix_analysis_runs_history", "ix_analysis_runs_request_id"}
    assert "(created_at_utc DESC, analysis_id DESC)" in definitions["ix_analysis_runs_history"]
    assert "UNIQUE" not in definitions["ix_analysis_runs_request_id"]
    assert "(request_id)" in definitions["ix_analysis_runs_request_id"]


def test_check_constraint_names_match_the_models(migrated):
    with migrated.connect() as connection:
        in_database = {
            name
            for (name,) in connection.execute(
                text("select conname from pg_constraint where conrelid = 'analysis_runs'::regclass and contype = 'c'")
            )
        }
    in_models = {c.name for c in AnalysisRunRow.__table__.constraints if isinstance(c, CheckConstraint)}

    assert in_database == in_models


def test_check_constraint_definitions_match_the_models(migrated):
    # alembic check ignores CHECK constraints, so build the model's schema aside and compare SQL.
    shadow = "model_shadow"
    query = text(
        "select conname, pg_get_constraintdef(oid) from pg_constraint"
        " where contype = 'c' and conrelid = to_regclass(:table)"
    )
    with migrated.connect() as connection:
        connection.execute(text(f"DROP SCHEMA IF EXISTS {shadow} CASCADE"))
        connection.execute(text(f"CREATE SCHEMA {shadow}"))
        connection.commit()
        try:
            shadow_connection = connection.execution_options(schema_translate_map={None: shadow})
            AnalysisRunRow.metadata.create_all(shadow_connection)
            from_models = dict(connection.execute(query, {"table": f"{shadow}.analysis_runs"}).all())
            from_migration = dict(connection.execute(query, {"table": "public.analysis_runs"}).all())
        finally:
            connection.rollback()
            connection.execute(text(f"DROP SCHEMA IF EXISTS {shadow} CASCADE"))
            connection.commit()

    assert from_models and from_models == from_migration


def test_alembic_check_finds_no_pending_differences(migrated, alembic_config):
    command.check(alembic_config)


def test_alembic_check_detects_real_drift(restore_head, alembic_config):
    with restore_head.begin() as connection:
        connection.execute(text("alter table analysis_runs add column drift integer"))

    try:
        with pytest.raises(CommandError):
            command.check(alembic_config)
    finally:
        with restore_head.begin() as connection:
            connection.execute(text("alter table analysis_runs drop column drift"))


def test_downgrade_removes_everything_and_upgrade_restores_it(restore_head, alembic_config):
    command.downgrade(alembic_config, "base")

    assert "analysis_runs" not in _tables(restore_head)
    assert "alembic_version" in _tables(restore_head)

    command.upgrade(alembic_config, "head")

    assert "analysis_runs" in _tables(restore_head)
    command.check(alembic_config)
