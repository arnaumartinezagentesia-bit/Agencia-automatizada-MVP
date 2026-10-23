from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.api import schemas
from app.domain.market import MarketSnapshot
from app.domain.run import AnalysisRun, AnalysisSummary
from app.persistence.errors import CorruptRowError
from app.persistence.mapping import row_to_failure_snapshot, row_to_run, row_to_summary, run_to_values

STATUSES = ["pending", "running", "completed", "failed"]


def _row(values, **overrides):
    return SimpleNamespace(**{**values, **overrides})


def _values(make, status, snapshot=None):
    run = AnalysisRun.model_validate(make.run(status))
    return run, run_to_values(run, snapshot)


@pytest.mark.parametrize("status", STATUSES)
def test_round_trip_reconstructs_an_equal_run(make, status):
    run, values = _values(make, status)

    assert row_to_run(_row(values)) == run


def test_failed_run_round_trips_with_and_without_snapshot(make):
    snapshot = MarketSnapshot.model_validate(make.snapshot())
    run, values = _values(make, "failed", snapshot)

    assert row_to_run(_row(values)) == run
    assert row_to_failure_snapshot(_row(values)) == snapshot
    assert row_to_failure_snapshot(_row(values, failure_snapshot=None)) is None


def test_json_payloads_keep_decimals_as_strings_and_timestamps_as_rfc3339(make):
    _, values = _values(make, "completed")

    bar = values["analysis"]["market_snapshot"]["bars"][0]
    assert bar["open"] == "3640.10" and isinstance(bar["open"], str)
    assert values["analysis"]["timestamp_utc"] == "2026-09-18T14:30:05Z"


def test_relational_columns_hold_request_fields_and_provenance_mode(make):
    run, values = _values(make, "completed")

    assert (values["symbol"], values["timeframe"], values["data_mode"]) == ("XAUUSD", "1h", "fixture")
    assert values["status"] == "completed"
    assert values["analysis"]["data_sources"][0]["mode"] == run.request.data_mode.value


def test_non_utc_offsets_are_normalized_to_utc(make):
    _, values = _values(make, "running")
    plus_two = timezone(timedelta(hours=2))
    values["created_at_utc"] = values["created_at_utc"].astimezone(plus_two)
    values["started_at_utc"] = values["started_at_utc"].astimezone(plus_two)

    run = row_to_run(_row(values))

    assert run.created_at_utc.utcoffset() == timedelta(0)
    assert run.created_at_utc == datetime(2026, 9, 18, 14, 30, tzinfo=UTC)


def test_naive_timestamps_are_rejected(make):
    _, values = _values(make, "running")
    values["started_at_utc"] = values["started_at_utc"].replace(tzinfo=None)

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values))


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "completed", "completed_at_utc": None},
        {"status": "failed"},
        {"status": "pending"},
        {"status": "unknown"},
        {"symbol": "EURUSD"},
        {"timeframe": "2h"},
        {"data_mode": "live"},  # requested mode differs from the analysis provenance
        {"error": {"code": "PROVIDER_ERROR", "message": "x"}},
    ],
)
def test_inconsistent_completed_rows_are_rejected(make, overrides):
    _, values = _values(make, "completed")

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values, **overrides))


def test_analysis_id_mismatch_between_row_and_json_is_rejected(make):
    _, values = _values(make, "completed")
    values["analysis"] = {**values["analysis"], "analysis_id": "11111111-1111-4111-8111-111111111111"}

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values))


def test_completed_at_must_equal_analysis_timestamp(make):
    _, values = _values(make, "completed")
    values["completed_at_utc"] = values["completed_at_utc"] + timedelta(seconds=1)

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values))


@pytest.mark.parametrize("bad_json", [[], "text", 3, {}, {"analysis_id": None}])
def test_invalid_analysis_json_is_rejected(make, bad_json):
    _, values = _values(make, "completed")

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values, analysis=bad_json))


def test_invalid_error_json_is_rejected(make):
    _, values = _values(make, "failed")

    with pytest.raises(CorruptRowError):
        row_to_run(_row(values, error={"code": "NOT_A_CODE", "message": "x"}))


def test_invalid_failure_snapshot_is_reported_only_by_the_internal_accessor(make):
    run, values = _values(make, "failed", MarketSnapshot.model_validate(make.snapshot()))

    # A damaged diagnostic blob must not make the public run unreadable...
    assert row_to_run(_row(values, failure_snapshot={"symbol": "XAUUSD"})) == run
    # ...but it is never silently trusted when read as a snapshot.
    with pytest.raises(CorruptRowError):
        row_to_failure_snapshot(_row(values, failure_snapshot={"symbol": "XAUUSD"}))
    with pytest.raises(CorruptRowError):
        row_to_failure_snapshot(_row(values, failure_snapshot=[1]))


def test_corrupt_row_error_keeps_no_context_holding_the_payload(make):
    _, values = _values(make, "completed")
    values["analysis"]["trend_context"]["description"] = "TOP-SECRET-PAYLOAD"
    values["analysis"]["trend_context"]["direction"] = "sideways-ish"

    with pytest.raises(CorruptRowError) as info:
        row_to_run(_row(values))

    assert info.value.__cause__ is None and info.value.__context__ is None


def test_corrupt_row_error_reports_locations_not_values(make):
    _, values = _values(make, "completed")
    values["analysis"]["trend_context"]["description"] = "TOP-SECRET-PAYLOAD"
    values["analysis"]["trend_context"]["direction"] = "sideways-ish"

    with pytest.raises(CorruptRowError) as info:
        row_to_run(_row(values))

    assert "TOP-SECRET-PAYLOAD" not in str(info.value)
    assert "trend_context" in str(info.value)


def test_summary_uses_created_at_and_requested_mode(make):
    run, values = _values(make, "failed")

    summary = row_to_summary(_row(values))

    assert summary == AnalysisSummary(
        analysis_id=run.analysis_id,
        symbol=run.request.symbol,
        timeframe=run.request.timeframe,
        status=run.status,
        timestamp_utc=run.created_at_utc,
        data_source_mode=run.request.data_mode,
    )


def test_summary_rejects_unknown_status(make):
    _, values = _values(make, "pending")

    with pytest.raises(CorruptRowError):
        row_to_summary(_row(values, status="archived"))


def test_failure_snapshot_is_not_part_of_any_public_contract():
    assert "failure_snapshot" not in AnalysisRun.model_fields
    assert "failure_snapshot" not in AnalysisSummary.model_fields
    for name in dir(schemas):
        model = getattr(schemas, name)
        fields = getattr(model, "model_fields", {})
        assert "failure_snapshot" not in fields, name
