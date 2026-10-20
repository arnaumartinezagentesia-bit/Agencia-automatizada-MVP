import pytest
from pydantic import ValidationError

from app.domain.run import AnalysisRequest, AnalysisRun, AnalysisSummary

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]


@pytest.mark.parametrize("timeframe", TIMEFRAMES)
@pytest.mark.parametrize("mode", ["fixture", "live"])
def test_request_accepts_every_timeframe_and_mode(timeframe, mode):
    req = AnalysisRequest.model_validate({"symbol": "XAUUSD", "timeframe": timeframe, "data_mode": mode})
    assert req.timeframe.value == timeframe and req.data_mode.value == mode


@pytest.mark.parametrize(
    "changes",
    [
        {"symbol": "XAU/USD"},
        {"symbol": "xauusd"},
        {"symbol": "EURUSD"},
        {"symbol": ""},
        {"timeframe": "2h"},
        {"timeframe": "1H"},
        {"timeframe": 60},
        {"data_mode": "demo"},
        {"data_mode": "Live"},
        {"symbol": None},
        {"timeframe": None},
        {"data_mode": None},
    ],
)
def test_invalid_request_values(make, changes):
    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate({**make.request(), **changes})


@pytest.mark.parametrize("field", ["symbol", "timeframe", "data_mode"])
def test_request_requires_every_field(make, field):
    data = make.request()
    del data[field]
    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate(data)


@pytest.mark.parametrize(
    "extra", ["model", "prompt", "status", "provider", "api_key", "broker", "action", "position_size", "order"]
)
def test_request_rejects_undefined_fields(make, extra):
    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate({**make.request(), extra: "x"})


@pytest.mark.parametrize("status", ["pending", "running", "completed", "failed"])
def test_valid_run_for_each_status(make, status):
    run = AnalysisRun.model_validate(make.run(status))
    assert run.status.value == status


@pytest.mark.parametrize("status", ["pending", "running", "completed", "failed"])
def test_run_serializes_contract_nulls_and_round_trips(make, status):
    run = AnalysisRun.model_validate(make.run(status))
    expected = make.run(status)
    if expected["error"]:
        expected["error"]["details"] = None  # optional field, serialized as null
    assert run.model_dump(mode="json") == expected  # includes every null the status requires
    assert AnalysisRun.model_validate_json(run.model_dump_json()) == run


def _bad(make, status, **changes):
    return {**make.run(status), **changes}


@pytest.mark.parametrize(
    ("status", "changes"),
    [
        # pending: everything except created_at must be null
        ("pending", {"started_at_utc": "2026-09-18T14:30:00Z"}),
        ("pending", {"completed_at_utc": "2026-09-18T14:30:05Z"}),
        ("pending", {"failed_at_utc": "2026-09-18T14:30:05Z"}),
        ("pending", {"error": {"code": "PROVIDER_ERROR", "message": "x"}}),
        # running
        ("running", {"started_at_utc": None}),
        ("running", {"completed_at_utc": "2026-09-18T14:30:05Z"}),
        ("running", {"failed_at_utc": "2026-09-18T14:30:05Z"}),
        ("running", {"error": {"code": "PROVIDER_ERROR", "message": "x"}}),
        # completed
        ("completed", {"started_at_utc": None}),
        ("completed", {"completed_at_utc": None}),
        ("completed", {"failed_at_utc": "2026-09-18T14:30:05Z"}),
        ("completed", {"analysis": None}),
        ("completed", {"error": {"code": "PROVIDER_ERROR", "message": "x"}}),
        # failed
        ("failed", {"started_at_utc": None}),
        ("failed", {"failed_at_utc": None}),
        ("failed", {"completed_at_utc": "2026-09-18T14:30:05Z"}),
        ("failed", {"error": None}),
    ],
)
def test_invalid_lifecycle_combinations(make, status, changes):
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(_bad(make, status, **changes))


def test_failed_run_rejects_an_analysis(make):
    data = _bad(make, "failed", analysis=make.analysis())
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


def test_pending_run_rejects_an_analysis(make):
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(_bad(make, "pending", analysis=make.analysis()))


def test_unknown_status_rejected(make):
    for status in ("idle", "submitting"):
        with pytest.raises(ValidationError):
            AnalysisRun.model_validate({**make.run("pending"), "status": status})


def test_completed_requires_matching_completion_timestamp(make):
    data = make.run("completed")
    data["completed_at_utc"] = "2026-09-18T14:30:06Z"
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


def test_completed_requires_matching_analysis_id(make):
    data = make.run("completed")
    data["analysis"]["analysis_id"] = "11111111-1111-4111-8111-111111111111"
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


def test_completed_requires_matching_data_mode(make):
    data = make.run("completed")
    data["request"]["data_mode"] = "live"  # analysis provenance says fixture
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


def test_completed_live_run_requires_live_provenance_everywhere(make):
    data = make.run("completed")
    live = {**make.source(), "mode": "live"}
    data["request"]["data_mode"] = "live"
    data["analysis"]["market_snapshot"]["data_source"] = live
    data["analysis"]["data_sources"] = [live]
    AnalysisRun.model_validate(data)
    data["analysis"]["data_sources"] = [live, make.source()]  # a fixture source sneaks in
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


@pytest.mark.parametrize("field", ["analysis_id", "status", "created_at_utc", "request_id", "request"])
def test_run_requires_core_fields(make, field):
    data = make.run("pending")
    del data[field]
    with pytest.raises(ValidationError):
        AnalysisRun.model_validate(data)


def test_run_ids_are_uuid4_and_timestamps_utc(make):
    for changes in [
        {"analysis_id": "7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e"},
        {"request_id": "nope"},
        {"created_at_utc": "2026-09-18T14:30:00"},
        {"created_at_utc": "2026-09-18T16:30:00+02:00"},
    ]:
        with pytest.raises(ValidationError):
            AnalysisRun.model_validate(_bad(make, "pending", **changes))


@pytest.mark.parametrize(
    "bad_id",
    [
        "7c2e1ef61c884a3a87f5f3d5c9a0f11e",
        "{7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e}",
        "urn:uuid:7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e\n",
        5,
        b"7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
    ],
)
def test_run_rejects_non_canonical_uuid_inputs(make, bad_id):
    for field in ("analysis_id", "request_id"):
        with pytest.raises(ValidationError):
            AnalysisRun.model_validate(_bad(make, "pending", **{field: bad_id}))


def test_run_accepts_uppercase_uuid_and_serializes_lowercase(make):
    data = make.run("pending")
    data["analysis_id"] = data["analysis_id"].upper()
    assert AnalysisRun.model_validate(data).model_dump(mode="json")["analysis_id"] == make.run("pending")["analysis_id"]


def test_run_has_no_lifecycle_methods():
    public = {n for n in dir(AnalysisRun) if not n.startswith("_") and callable(getattr(AnalysisRun, n))}
    assert not {n for n in public if "transition" in n or n.startswith(("start", "complete", "fail"))}


def _summary():
    return {
        "analysis_id": "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "status": "completed",
        "timestamp_utc": "2026-09-18T14:30:00Z",
        "data_source_mode": "fixture",
    }


@pytest.mark.parametrize("status", ["pending", "running", "completed", "failed"])
def test_summary_valid_for_every_status(status):
    s = AnalysisSummary.model_validate({**_summary(), "status": status})
    assert AnalysisSummary.model_validate_json(s.model_dump_json()) == s


@pytest.mark.parametrize("field", list(_summary()))
def test_summary_requires_every_field(field):
    data = _summary()
    del data[field]
    with pytest.raises(ValidationError):
        AnalysisSummary.model_validate(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "idle"},
        {"data_source_mode": "demo"},
        {"symbol": "EURUSD"},
        {"timeframe": "3m"},
        {"timestamp_utc": "2026-09-18T14:30:00"},
        {"analysis_id": "nope"},
        {"completed_at_utc": "2026-09-18T14:30:05Z"},
    ],
)
def test_invalid_summary(changes):
    with pytest.raises(ValidationError):
        AnalysisSummary.model_validate({**_summary(), **changes})
