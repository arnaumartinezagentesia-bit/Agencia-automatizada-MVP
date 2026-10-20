import json
import uuid

import pytest
from pydantic import TypeAdapter, ValidationError

from app.api.schemas import (
    CreateAnalysisData,
    ErrorEnvelope,
    GetAnalysisCompletedData,
    GetAnalysisData,
    GetAnalysisFailedData,
    GetAnalysisPendingData,
    GetAnalysisRunningData,
    ListAnalysesData,
    Pagination,
    ResponseMeta,
    SuccessEnvelope,
)
from app.domain.enums import ErrorCode

AID = "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e"
META = {"request_id": "c9c52d62-5e0b-4a11-bc61-89e7a9f4e9b4"}
GET = TypeAdapter(GetAnalysisData)


def test_meta_requires_uuid4():
    ResponseMeta.model_validate(META)
    for bad in [{"request_id": "nope"}, {"request_id": "7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e"}, {}, {**META, "x": 1}]:
        with pytest.raises(ValidationError):
            ResponseMeta.model_validate(bad)


def test_create_response_envelope():
    env = SuccessEnvelope[CreateAnalysisData].model_validate({"data": {"analysis_id": AID, "status": "completed"}, "meta": META})
    assert env.model_dump(mode="json") == {"data": {"analysis_id": AID, "status": "completed"}, "meta": META}


@pytest.mark.parametrize("status", ["failed", "pending", "running", "idle", ""])
def test_create_response_only_accepts_completed(status):
    with pytest.raises(ValidationError):
        CreateAnalysisData.model_validate({"analysis_id": AID, "status": status})


@pytest.mark.parametrize("data", [[], [{"analysis_id": AID, "status": "completed"}], "text", None, 5])
def test_envelope_data_must_be_an_object(data):
    with pytest.raises(ValidationError):
        SuccessEnvelope[CreateAnalysisData].model_validate({"data": data, "meta": META})


def test_envelope_requires_meta_and_rejects_extras():
    good = {"data": {"analysis_id": AID, "status": "completed"}, "meta": META}
    for bad in [{"data": good["data"]}, {**good, "extra": 1}]:
        with pytest.raises(ValidationError):
            SuccessEnvelope[CreateAnalysisData].model_validate(bad)


def test_get_pending_and_running_have_null_analysis_and_error():
    for status, cls in [("pending", GetAnalysisPendingData), ("running", GetAnalysisRunningData)]:
        parsed = GET.validate_python({"analysis_id": AID, "status": status, "analysis": None, "error": None})
        assert isinstance(parsed, cls)
        assert GET.dump_python(parsed, mode="json") == {"analysis_id": AID, "status": status, "analysis": None, "error": None}


def test_get_completed_requires_analysis(make):
    ok = {"analysis_id": AID, "status": "completed", "analysis": make.analysis(), "error": None}
    assert isinstance(GET.validate_python(ok), GetAnalysisCompletedData)
    with pytest.raises(ValidationError):
        GET.validate_python({**ok, "analysis": None})
    with pytest.raises(ValidationError):
        GET.validate_python({**ok, "error": {"code": "PROVIDER_ERROR", "message": "m"}})


def test_get_failed_requires_error_and_no_analysis(make):
    ok = {"analysis_id": AID, "status": "failed", "analysis": None, "error": {"code": "PROVIDER_ERROR", "message": "m"}}
    parsed = GET.validate_python(ok)
    assert isinstance(parsed, GetAnalysisFailedData)
    assert GET.dump_python(parsed, mode="json")["error"]["details"] is None
    with pytest.raises(ValidationError):
        GET.validate_python({**ok, "error": None})
    with pytest.raises(ValidationError):
        GET.validate_python({**ok, "analysis": make.analysis()})


@pytest.mark.parametrize("status", ["pending", "running"])
def test_get_pending_running_reject_payloads(make, status):
    base = {"analysis_id": AID, "status": status, "analysis": None, "error": None}
    with pytest.raises(ValidationError):
        GET.validate_python({**base, "analysis": make.analysis()})
    with pytest.raises(ValidationError):
        GET.validate_python({**base, "error": {"code": "LLM_ERROR", "message": "m"}})


def test_get_rejects_unknown_status_and_missing_discriminator():
    for bad in [{"analysis_id": AID, "status": "idle"}, {"analysis_id": AID}, {"analysis_id": AID, "status": "submitting"}]:
        with pytest.raises(ValidationError):
            GET.validate_python(bad)


OTHER_AID = "8f0a7f29-0f8e-4b0f-93c7-f4c6e2bf56c2"


def _completed(make, analysis_id=AID, inner_id=AID):
    analysis = make.analysis()
    analysis["analysis_id"] = inner_id
    return {"analysis_id": analysis_id, "status": "completed", "analysis": analysis, "error": None}


def test_get_completed_accepts_matching_ids(make):
    parsed = GetAnalysisCompletedData.model_validate(_completed(make))
    assert parsed.analysis_id == parsed.analysis.analysis_id


def test_get_completed_matches_ids_regardless_of_hex_case(make):
    parsed = GetAnalysisCompletedData.model_validate(_completed(make, analysis_id=AID.upper()))
    assert parsed.analysis_id == parsed.analysis.analysis_id
    assert parsed.model_dump(mode="json")["analysis_id"] == AID


def test_get_completed_rejects_mismatched_ids(make):
    with pytest.raises(ValidationError, match="analysis_id must match analysis.analysis_id"):
        GetAnalysisCompletedData.model_validate(_completed(make, inner_id=OTHER_AID))


def test_get_union_enforces_completed_id_match(make):
    assert isinstance(GET.validate_python(_completed(make)), GetAnalysisCompletedData)
    with pytest.raises(ValidationError, match="analysis_id must match analysis.analysis_id"):
        GET.validate_python(_completed(make, inner_id=OTHER_AID))


def test_get_union_enforces_completed_id_match_from_json(make):
    assert isinstance(GET.validate_json(json.dumps(_completed(make))), GetAnalysisCompletedData)
    with pytest.raises(ValidationError, match="analysis_id must match analysis.analysis_id"):
        GET.validate_json(json.dumps(_completed(make, inner_id=OTHER_AID)))


def test_success_envelope_enforces_completed_id_match(make):
    envelope = SuccessEnvelope[GetAnalysisData]
    assert envelope.model_validate({"data": _completed(make), "meta": META}).data.analysis_id == uuid.UUID(AID)
    with pytest.raises(ValidationError, match="analysis_id must match analysis.analysis_id"):
        envelope.model_validate({"data": _completed(make, inner_id=OTHER_AID), "meta": META})
    with pytest.raises(ValidationError, match="analysis_id must match analysis.analysis_id"):
        envelope.model_validate_json(json.dumps({"data": _completed(make, inner_id=OTHER_AID), "meta": META}))


def test_get_non_completed_states_are_unaffected_by_id_check(make):
    pending = GET.validate_python({"analysis_id": OTHER_AID, "status": "pending"})
    running = GET.validate_python({"analysis_id": OTHER_AID, "status": "running"})
    failed = GET.validate_python(
        {"analysis_id": OTHER_AID, "status": "failed", "error": {"code": "PROVIDER_ERROR", "message": "m"}}
    )
    assert [type(x) for x in (pending, running, failed)] == [
        GetAnalysisPendingData,
        GetAnalysisRunningData,
        GetAnalysisFailedData,
    ]


@pytest.mark.parametrize(
    "bad_id",
    ["7c2e1ef61c884a3a87f5f3d5c9a0f11e", "{" + AID + "}", "urn:uuid:" + AID, AID + "\n", " " + AID, AID[:-1]],
)
def test_schemas_reject_non_canonical_uuid_formats(make, bad_id):
    with pytest.raises(ValidationError):
        ResponseMeta.model_validate({"request_id": bad_id})
    with pytest.raises(ValidationError):
        CreateAnalysisData.model_validate({"analysis_id": bad_id, "status": "completed"})
    with pytest.raises(ValidationError):
        GET.validate_python({"analysis_id": bad_id, "status": "pending"})
    with pytest.raises(ValidationError):
        GET.validate_json(json.dumps({"analysis_id": bad_id, "status": "pending"}))
    with pytest.raises(ValidationError):
        GetAnalysisCompletedData.model_validate(_completed(make, analysis_id=AID, inner_id=bad_id))


def test_schemas_accept_uppercase_uuid_and_serialize_lowercase():
    meta = ResponseMeta.model_validate({"request_id": META["request_id"].upper()})
    assert meta.model_dump(mode="json") == META
    assert ResponseMeta.model_validate_json(json.dumps({"request_id": META["request_id"].upper()})) == meta


def test_get_envelope_round_trip(make):
    raw = {"data": {"analysis_id": AID, "status": "completed", "analysis": make.analysis(), "error": None}, "meta": META}
    env = SuccessEnvelope[GetAnalysisData].model_validate(raw)
    assert env.model_dump(mode="json") == raw
    assert SuccessEnvelope[GetAnalysisData].model_validate_json(env.model_dump_json()) == env


def _summary(status="completed"):
    return {
        "analysis_id": AID,
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "status": status,
        "timestamp_utc": "2026-09-18T14:30:00Z",
        "data_source_mode": "fixture",
    }


def test_list_response_round_trip():
    raw = {"items": [_summary(), _summary("failed")], "pagination": {"limit": 20, "offset": 0, "has_more": False}}
    data = ListAnalysesData.model_validate(raw)
    assert data.model_dump(mode="json") == raw
    assert ListAnalysesData.model_validate({**raw, "items": []}).items == []


def test_list_items_are_summaries_only():
    with pytest.raises(ValidationError):
        ListAnalysesData.model_validate(
            {"items": [{**_summary(), "analysis": {}}], "pagination": {"limit": 20, "offset": 0, "has_more": False}}
        )


@pytest.mark.parametrize(("limit", "offset"), [(1, 0), (20, 0), (20, 40), (10_000, 0)])
def test_pagination_valid_without_max_limit(limit, offset):
    assert Pagination(limit=limit, offset=offset, has_more=True).limit == limit


@pytest.mark.parametrize(
    "bad",
    [
        {"limit": 0, "offset": 0, "has_more": False},
        {"limit": -1, "offset": 0, "has_more": False},
        {"limit": 20, "offset": -1, "has_more": False},
        {"limit": "20", "offset": 0, "has_more": False},
        {"limit": 1.5, "offset": 0, "has_more": False},
        {"limit": 20, "offset": 0, "has_more": "yes"},
        {"limit": 20, "offset": 0},
        {"limit": 20, "offset": 0, "has_more": False, "total": 5},
    ],
)
def test_invalid_pagination(bad):
    with pytest.raises(ValidationError):
        Pagination.model_validate(bad)


@pytest.mark.parametrize("code", list(ErrorCode))
def test_error_envelope_for_every_code(code):
    raw = {"error": {"code": code.value, "message": "Safe message.", "details": {"field": "timeframe"}}, "meta": META}
    env = ErrorEnvelope.model_validate(raw)
    assert env.model_dump(mode="json") == raw
    assert ErrorEnvelope.model_validate_json(env.model_dump_json()) == env


@pytest.mark.parametrize(
    "bad",
    [
        {"meta": META},
        {"error": {"code": "VALIDATION_ERROR", "message": "m"}},
        {"error": {"code": "BOOM", "message": "m"}, "meta": META},
        {"error": {"code": "VALIDATION_ERROR", "message": "m"}, "meta": {"request_id": "x"}},
        {"error": {"code": "VALIDATION_ERROR", "message": "m"}, "meta": META, "data": {}},
    ],
)
def test_invalid_error_envelope(bad):
    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(bad)


def test_schemas_module_has_no_routes_or_handlers():
    import app.api.schemas as module

    names = {n.lower() for n in dir(module)}
    assert not {n for n in names if "router" in n or "handler" in n}
