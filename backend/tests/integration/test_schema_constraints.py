"""PostgreSQL itself must reject invalid rows, regardless of what the Python layer does."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import JSON, insert, null
from sqlalchemy.exc import IntegrityError

from tests.integration.conftest import TABLE

T0 = datetime(2026, 9, 18, 14, 30, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(seconds=5)
ERROR = {"code": "PROVIDER_ERROR", "message": "Market data provider failed."}
SNAPSHOT = {"symbol": "XAUUSD"}
MATCHING_ANALYSIS = "matching-analysis"  # replaced by a JSON whose analysis_id equals the row's


def _analysis(analysis_id):
    return {"analysis_id": str(analysis_id), "schema_version": "1.0.0"}


def _row(status, /, **overrides):
    """A row that satisfies every constraint for `status`, with overrides applied on top."""
    analysis_id = overrides.pop("analysis_id", uuid.uuid4())
    base = {
        "analysis_id": analysis_id,
        "request_id": uuid.uuid4(),
        "status": status,
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "data_mode": "fixture",
        "created_at_utc": T0,
        "started_at_utc": None,
        "completed_at_utc": None,
        "failed_at_utc": None,
        "error": null(),
        "analysis": null(),
        "failure_snapshot": null(),
    }
    if status in ("running", "completed", "failed"):
        base["started_at_utc"] = T0
    if status == "completed":
        base.update(completed_at_utc=T1, analysis=_analysis(analysis_id))
    if status == "failed":
        base.update(failed_at_utc=T1, error=ERROR)
    row = {**base, **overrides}
    if row["analysis"] == MATCHING_ANALYSIS:
        row["analysis"] = _analysis(analysis_id)
    return row


def _insert(engine, row):
    with engine.begin() as connection:
        connection.execute(insert(TABLE).values(**row))


def _violated(engine, row):
    with pytest.raises(IntegrityError) as info:
        _insert(engine, row)
    return info.value.orig.diag.constraint_name


@pytest.mark.parametrize("status", ["pending", "running", "completed", "failed"])
def test_valid_rows_of_every_state_are_accepted(db, status):
    _insert(db, _row(status))


def test_failed_row_accepts_a_failure_snapshot(db):
    _insert(db, _row("failed", failure_snapshot=SNAPSHOT))


LIFECYCLE = "ck_analysis_runs_lifecycle"
TEMPORAL = {"ck_analysis_runs_completed_after_started", "ck_analysis_runs_failed_after_started"}
INVALID_LIFECYCLE = {
    "pending with started_at": ("pending", {"started_at_utc": T0}),
    "pending with completed_at": ("pending", {"completed_at_utc": T1}),
    "pending with failed_at": ("pending", {"failed_at_utc": T1}),
    "pending with error": ("pending", {"error": ERROR}),
    "pending with analysis": ("pending", {"analysis": MATCHING_ANALYSIS}),
    "running without started_at": ("running", {"started_at_utc": None}),
    "running with completed_at": ("running", {"completed_at_utc": T1}),
    "running with failed_at": ("running", {"failed_at_utc": T1}),
    "running with error": ("running", {"error": ERROR}),
    "completed without started_at": ("completed", {"started_at_utc": None}),
    "completed without completed_at": ("completed", {"completed_at_utc": None}),
    "completed without analysis": ("completed", {"analysis": null()}),
    "completed with failed_at": ("completed", {"failed_at_utc": T1}),
    "completed with error": ("completed", {"error": ERROR}),
    "failed without started_at": ("failed", {"started_at_utc": None}),
    "failed without failed_at": ("failed", {"failed_at_utc": None}),
    "failed without error": ("failed", {"error": null()}),
    "failed with completed_at": ("failed", {"completed_at_utc": T1}),
    "failed with analysis": ("failed", {"analysis": MATCHING_ANALYSIS}),
}


@pytest.mark.parametrize("status, overrides", INVALID_LIFECYCLE.values(), ids=INVALID_LIFECYCLE.keys())
def test_invalid_lifecycle_combinations_are_rejected(db, status, overrides):
    # Several constraints can forbid the same row; PostgreSQL reports the first by name.
    assert _violated(db, _row(status, **overrides)) in {LIFECYCLE, *TEMPORAL}


@pytest.mark.parametrize("status", ["pending", "running", "completed"])
def test_failure_snapshot_is_only_allowed_on_failed_runs(db, status):
    # Both the lifecycle and the dedicated constraint forbid it; either may be reported first.
    assert _violated(db, _row(status, failure_snapshot=SNAPSHOT)) in {
        LIFECYCLE,
        "ck_analysis_runs_failure_snapshot_only_failed",
    }


@pytest.mark.parametrize(
    "column, value, constraint",
    [
        ("status", "archived", "ck_analysis_runs_status_valid"),
        ("symbol", "EURUSD", "ck_analysis_runs_symbol_valid"),
        ("timeframe", "2h", "ck_analysis_runs_timeframe_valid"),
        ("data_mode", "demo", "ck_analysis_runs_data_mode_valid"),
    ],
)
def test_enumerated_columns_reject_unknown_values(db, column, value, constraint):
    violated = _violated(db, _row("pending", **{column: value}))

    assert violated in {constraint, LIFECYCLE}


@pytest.mark.parametrize("column", ["request_id", "status", "symbol", "timeframe", "data_mode", "created_at_utc"])
def test_required_columns_are_not_null(db, column):
    with pytest.raises(IntegrityError) as info:
        _insert(db, _row("pending", **{column: None}))

    assert info.value.orig.diag.column_name == column


def test_analysis_json_without_an_analysis_id_cannot_slip_through_null_semantics(db):
    # `analysis ->> 'analysis_id'` is NULL here; a bare comparison would evaluate to NULL and pass.
    row = _row("completed", analysis={"schema_version": "1.0.0"})

    assert _violated(db, row) == "ck_analysis_runs_analysis_id_matches_row"


def test_analysis_json_with_null_analysis_id_is_rejected(db):
    assert _violated(db, _row("completed", analysis={"analysis_id": None})) == (
        "ck_analysis_runs_analysis_id_matches_row"
    )


def test_analysis_id_in_json_must_match_the_row(db):
    row = _row("completed", analysis=_analysis(uuid.uuid4()))

    assert _violated(db, row) == "ck_analysis_runs_analysis_id_matches_row"


def test_analysis_id_comparison_is_case_sensitive_to_canonical_lowercase(db):
    analysis_id = uuid.uuid4()
    row = _row("completed", analysis_id=analysis_id, analysis={"analysis_id": str(analysis_id).upper()})

    assert _violated(db, row) == "ck_analysis_runs_analysis_id_matches_row"


def test_analysis_must_be_a_json_object(db):
    violated = _violated(db, _row("completed", analysis=["not", "an", "object"]))

    assert violated in {"ck_analysis_runs_analysis_is_object", "ck_analysis_runs_analysis_id_matches_row"}


def test_error_must_be_a_json_object(db):
    assert _violated(db, _row("failed", error=["x"])) == "ck_analysis_runs_error_is_object"


def test_failure_snapshot_must_be_a_json_object(db):
    assert _violated(db, _row("failed", failure_snapshot="text")) == (
        "ck_analysis_runs_failure_snapshot_is_object"
    )


def test_json_null_is_not_accepted_as_a_missing_value(db):
    # The JSON literal `null` is a value, not SQL NULL: a pending row must not carry it.
    assert _violated(db, _row("pending", error=JSON.NULL)) in {
        LIFECYCLE,
        "ck_analysis_runs_error_is_object",
    }


def test_started_cannot_precede_creation(db):
    row = _row("running", started_at_utc=T0 - timedelta(seconds=1))

    assert _violated(db, row) == "ck_analysis_runs_started_after_created"


def test_completed_cannot_precede_start(db):
    row = _row("completed", started_at_utc=T1, completed_at_utc=T0, created_at_utc=T0)

    assert _violated(db, row) == "ck_analysis_runs_completed_after_started"


def test_failed_cannot_precede_start(db):
    row = _row("failed", started_at_utc=T1, failed_at_utc=T0)

    assert _violated(db, row) == "ck_analysis_runs_failed_after_started"


def test_primary_key_is_unique(db):
    row = _row("pending")
    _insert(db, row)

    assert _violated(db, {**row, "request_id": uuid.uuid4()}) == "pk_analysis_runs"


def test_request_id_is_not_unique(db):
    shared = uuid.uuid4()
    _insert(db, _row("pending", request_id=shared))
    _insert(db, _row("pending", request_id=shared))
