import pytest
from pydantic import ValidationError

from app.domain.enums import ErrorCode
from app.domain.errors import ErrorDetail


@pytest.mark.parametrize("code", list(ErrorCode))
def test_every_error_code_is_accepted(code):
    assert ErrorDetail.model_validate({"code": code.value, "message": "Safe message."}).code is code


def test_details_is_optional_and_nullable():
    assert ErrorDetail(code="NOT_FOUND", message="x").details is None
    assert ErrorDetail(code="NOT_FOUND", message="x", details=None).details is None
    assert ErrorDetail(code="VALIDATION_ERROR", message="x", details={"field": "timeframe"}).details == {
        "field": "timeframe"
    }


@pytest.mark.parametrize("details", [[1], "text", 5])
def test_details_must_be_an_object(details):
    with pytest.raises(ValidationError):
        ErrorDetail(code="NOT_FOUND", message="x", details=details)


@pytest.mark.parametrize(
    "payload",
    [
        {"code": "NOPE", "message": "x"},
        {"code": "NOT_FOUND", "message": ""},
        {"code": "NOT_FOUND"},
        {"message": "x"},
        {"code": "NOT_FOUND", "message": "x", "stack_trace": "boom"},
    ],
)
def test_invalid_error_detail(payload):
    with pytest.raises(ValidationError):
        ErrorDetail.model_validate(payload)


def test_json_round_trip_keeps_null_details():
    err = ErrorDetail(code="LLM_ERROR", message="Analysis engine unavailable.")
    assert ErrorDetail.model_validate_json(err.model_dump_json()) == err
    assert err.model_dump(mode="json") == {"code": "LLM_ERROR", "message": "Analysis engine unavailable.", "details": None}
