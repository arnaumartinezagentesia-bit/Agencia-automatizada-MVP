import pytest
from pydantic import TypeAdapter, ValidationError

from app.domain.enums import ErrorCode
from app.domain.events import (
    AnalysisCompletedEvent,
    AnalysisFailedEvent,
    AnalysisStartedEvent,
    WebSocketEvent,
)

ADAPTER = TypeAdapter(WebSocketEvent)
IDS = {
    "event_id": "8f0a7f29-0f8e-4b0f-93c7-f4c6e2bf56c2",
    "occurred_at": "2026-09-18T14:30:05Z",
    "analysis_id": "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
}


def _event(event_type, payload):
    return {**IDS, "event_type": event_type, "payload": payload}


VALID = [
    (_event("analysis.started", {"status": "running"}), AnalysisStartedEvent),
    (_event("analysis.completed", {"status": "completed"}), AnalysisCompletedEvent),
    (
        _event("analysis.failed", {"status": "failed", "error": {"code": "PROVIDER_ERROR", "message": "Market data provider failed."}}),
        AnalysisFailedEvent,
    ),
]


@pytest.mark.parametrize(("data", "cls"), VALID)
def test_valid_events_select_the_right_variant_and_round_trip(data, cls):
    event = ADAPTER.validate_python(data)
    assert isinstance(event, cls)
    assert ADAPTER.dump_python(event, mode="json") == data
    assert ADAPTER.validate_json(ADAPTER.dump_json(event)) == event


@pytest.mark.parametrize("code", list(ErrorCode))
def test_failed_event_accepts_every_error_code(code):
    ADAPTER.validate_python(_event("analysis.failed", {"status": "failed", "error": {"code": code.value, "message": "m"}}))


@pytest.mark.parametrize(
    "data",
    [
        _event("analysis.started", {"status": "completed"}),
        _event("analysis.started", {"status": "failed"}),
        _event("analysis.completed", {"status": "running"}),
        _event("analysis.completed", {"status": "failed", "error": {"code": "LLM_ERROR", "message": "m"}}),
        _event("analysis.failed", {"status": "failed"}),
        _event("analysis.failed", {"status": "completed"}),
        _event("analysis.failed", {"status": "failed", "error": {"code": "NOPE", "message": "m"}}),
        _event("analysis.failed", {"status": "failed", "error": {"code": "LLM_ERROR", "message": ""}}),
        _event("analysis.failed", {"status": "failed", "error": {"code": "LLM_ERROR", "message": "m", "details": {"x": 1}}}),
        _event("analysis.started", {"status": "running", "analysis": {"trend": "up"}}),
        _event("analysis.completed", {"status": "completed", "analysis": {}}),
        _event("analysis.cancelled", {"status": "running"}),
        _event("order.placed", {"status": "running"}),
        _event("analysis.started", None),
        _event("analysis.started", []),
    ],
)
def test_invalid_event_payloads(data):
    with pytest.raises(ValidationError):
        ADAPTER.validate_python(data)


@pytest.mark.parametrize("field", ["event_id", "event_type", "occurred_at", "analysis_id", "payload"])
def test_envelope_requires_every_field(field):
    data = dict(VALID[0][0])
    del data[field]
    with pytest.raises(ValidationError):
        ADAPTER.validate_python(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"event_id": "7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e"},
        {"analysis_id": "nope"},
        {"occurred_at": "2026-09-18T14:30:05"},
        {"occurred_at": "2026-09-18T16:30:05+02:00"},
        {"unexpected": 1},
    ],
)
def test_envelope_field_validation(changes):
    with pytest.raises(ValidationError):
        ADAPTER.validate_python({**VALID[0][0], **changes})
