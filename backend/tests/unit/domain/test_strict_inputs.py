"""F2-001 (UtcDatetime), F2-003 (str vs bytes) and F2-004 (JSON object) hardening."""

import json
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app.domain.analysis import KeyLevel, MarketAnalysis, ModelMetadata, TrendContext, VolatilityContext
from app.domain.errors import ErrorDetail
from app.domain.events import ErrorSummary
from app.domain.market import DataSource
from app.domain.run import AnalysisSummary
from app.domain.types import NonEmptyStr, UtcDatetime

UTC_ADAPTER = TypeAdapter(UtcDatetime)
STAMP = datetime(2026, 9, 18, 14, 30, tzinfo=UTC)

# ---------------------------------------------------------------- F2-001: UtcDatetime


@pytest.mark.parametrize(
    "value",
    [
        1758205800,
        1758205800.0,
        0,
        True,
        False,
        None,
        b"2026-09-18T14:30:00Z",
        "1758205800",
        "0",
        "",
        "2026-09-18",
        date(2026, 9, 18),
        "2026-09-18T14:30Z",
        "2026-09-18T14:30:00+0000",
        "2026-09-18T14:30:00+00",
        "2026-09-18 14:30:00Z",
        "2026-09-18T14:30:00",
        "2026-09-18T14:30:00 Z",
        " 2026-09-18T14:30:00Z",
        "2026-09-18T14:30:00Z\n",
        "2026-09-18T14:30:00.Z",
        "2026-9-18T14:30:00Z",
        "20260918T143000Z",
        "2026-09-18T14:30:00+02:00",
        "2026-09-18T09:30:00-05:00",
        "٢026-09-18T14:30:00Z",
        "2026-09-18T14:30:60Z",  # leap second: datetime cannot represent it
    ],
)
def test_utc_datetime_rejects_in_python_mode(value):
    with pytest.raises(ValidationError):
        UTC_ADAPTER.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "2026-09-18T14:30:00Z",
        "2026-09-18T14:30:00+00:00",
        "2026-09-18T14:30:00-00:00",  # RFC 3339 4.3: UTC instant, local offset unknown
        "2026-09-18t14:30:00z",  # RFC 3339 ABNF literals are case-insensitive
        "2026-09-18T14:30:00.5Z",
        "2026-09-18T14:30:00.123456+00:00",
        STAMP,
        datetime(2026, 9, 18, 14, 30, tzinfo=timezone(timedelta(0))),
    ],
)
def test_utc_datetime_accepts_and_returns_a_datetime(value):
    parsed = UTC_ADAPTER.validate_python(value)
    assert isinstance(parsed, datetime)
    assert parsed.utcoffset() == timedelta(0)
    assert parsed.replace(microsecond=0) == STAMP


@pytest.mark.parametrize(
    "raw",
    [
        "1758205800",
        "0",
        "true",
        "null",
        "1.5",
        '"1758205800"',
        '"0"',
        '"2026-09-18T14:30Z"',
        '"2026-09-18T14:30:00+0000"',
        '"2026-09-18 14:30:00Z"',
        '"2026-09-18T14:30:00"',
        '"2026-09-18T16:30:00+02:00"',
        '"2026-09-18"',
    ],
)
def test_utc_datetime_rejects_in_json_mode(raw):
    with pytest.raises(ValidationError):
        UTC_ADAPTER.validate_json(raw)


@pytest.mark.parametrize("raw", ['"2026-09-18T14:30:00Z"', '"2026-09-18T14:30:00+00:00"', '"2026-09-18t14:30:00z"'])
def test_utc_datetime_accepts_in_json_mode(raw):
    parsed = UTC_ADAPTER.validate_json(raw)
    assert isinstance(parsed, datetime) and parsed == STAMP


def test_utc_datetime_still_serializes_with_z():
    assert UTC_ADAPTER.dump_json(UTC_ADAPTER.validate_python("2026-09-18T14:30:00+00:00")) == b'"2026-09-18T14:30:00Z"'


def test_fractional_digits_beyond_microseconds_are_truncated_not_rounded():
    # Documented limitation: datetime keeps microseconds; finer input is truncated by the parser.
    parsed = UTC_ADAPTER.validate_python("2026-09-18T14:30:00.1234567Z")
    assert parsed.microsecond == 123456
    assert UTC_ADAPTER.validate_python("2026-09-18T14:30:00.9999999Z").microsecond == 999999


def _source(**changes):
    return {
        "mode": "fixture",
        "provider_name": "P",
        "provider_version": "1",
        "retrieved_at_utc": "2026-09-18T14:30:01Z",
        "source_as_of_utc": "2026-09-18T14:30:00Z",
        **changes,
    }


@pytest.mark.parametrize("bad", [1758205800, "1758205800", "0", "2026-09-18T14:30Z", "2026-09-18T14:30:00+0000", "2026-09-18 14:30:00Z"])
def test_domain_model_rejects_loose_timestamps_python_and_json(bad):
    with pytest.raises(ValidationError):
        DataSource.model_validate(_source(retrieved_at_utc=bad))
    with pytest.raises(ValidationError):
        DataSource.model_validate_json(json.dumps(_source(source_as_of_utc=bad)))


def test_domain_model_accepts_valid_timestamps_python_and_json():
    py = DataSource.model_validate(_source())
    assert py.retrieved_at_utc == datetime(2026, 9, 18, 14, 30, 1, tzinfo=UTC)
    assert DataSource.model_validate_json(json.dumps(_source())) == py
    assert DataSource.model_validate(_source(retrieved_at_utc=STAMP)).retrieved_at_utc == STAMP


def test_summary_rejects_epoch_timestamp_in_json():
    raw = {
        "analysis_id": "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "status": "pending",
        "timestamp_utc": 1758205800,
        "data_source_mode": "fixture",
    }
    with pytest.raises(ValidationError):
        AnalysisSummary.model_validate_json(json.dumps(raw))


# ---------------------------------------------------------------- F2-003: bytes are not text


@pytest.mark.parametrize("value", [b"text", bytearray(b"text"), 5, 1.5, None, ["a"]])
def test_non_empty_str_rejects_non_strings(value):
    with pytest.raises(ValidationError):
        TypeAdapter(NonEmptyStr).validate_python(value)


@pytest.mark.parametrize("value", ["text", " ", "  Mixed Case  "])
def test_non_empty_str_accepts_strings_unchanged(value):
    assert TypeAdapter(NonEmptyStr).validate_python(value) == value


def test_description_fields_reject_bytes_and_keep_valid_text():
    with pytest.raises(ValidationError):
        TrendContext(direction="up", strength="weak", description=b"bytes")
    with pytest.raises(ValidationError):
        VolatilityContext(regime="low", description=b"bytes")
    with pytest.raises(ValidationError):
        KeyLevel(type="support", price="1", description=b"bytes")
    assert TrendContext(direction="up", strength="weak", description="  ok ").description == "  ok "
    assert TrendContext(direction="up", strength="weak", description="x" * 2000).description == "x" * 2000


@pytest.mark.parametrize("field", ["market_observations", "uncertainties"])
def test_short_text_items_reject_bytes(make, field):
    data = make.analysis()
    data[field] = [b"bytes"]
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)
    data[field] = ["x" * 500]
    assert MarketAnalysis.model_validate(data)


def test_provider_and_model_strings_reject_bytes(make):
    for field in ("provider_name", "provider_version"):
        with pytest.raises(ValidationError):
            DataSource.model_validate(_source(**{field: b"x"}))
    for field in ("provider", "model", "prompt_version"):
        with pytest.raises(ValidationError):
            ModelMetadata.model_validate({**make.analysis()["model_metadata"], field: b"x"})


def test_error_messages_reject_bytes():
    with pytest.raises(ValidationError):
        ErrorDetail(code="LLM_ERROR", message=b"bytes")
    with pytest.raises(ValidationError):
        ErrorSummary(code="LLM_ERROR", message=b"bytes")


# ---------------------------------------------------------------- F2-004: ErrorDetail.details


def _err(details):
    return ErrorDetail(code="VALIDATION_ERROR", message="m", details=details)


VALID_DETAILS = [
    {},
    {"field": "timeframe"},
    {"s": "text", "i": 3, "f": 1.5, "t": True, "n": None, "empty": ""},
    {"list": [1, "a", None, False, 2.5, [], {}], "obj": {"deep": {"deeper": [{"x": 1}]}}},
    {"big": 12345678901234567890, "neg": -3, "zero": 0, "": "empty key is a valid JSON key"},
]


@pytest.mark.parametrize("details", VALID_DETAILS)
def test_details_accepts_valid_json_objects_and_preserves_content(details):
    err = _err(details)
    assert err.details == details
    dumped = err.model_dump(mode="json")
    assert dumped["details"] == details
    assert json.loads(err.model_dump_json())["details"] == details
    assert ErrorDetail.model_validate_json(err.model_dump_json()) == err


def test_details_none_and_default():
    assert _err(None).details is None
    assert ErrorDetail(code="NOT_FOUND", message="m").details is None
    assert json.loads(_err(None).model_dump_json())["details"] is None


@pytest.mark.parametrize(
    "bad",
    [
        {"v": object()},
        {"v": {1, 2}},
        {"v": frozenset({1})},
        {"v": datetime(2026, 9, 18, tzinfo=UTC)},
        {"v": date(2026, 9, 18)},
        {"v": Decimal("1.5")},
        {"v": (1, 2)},
        {"v": b"bytes"},
        {"v": bytearray(b"b")},
        {"v": complex(1, 2)},
        {"v": float("nan")},
        {"v": float("inf")},
        {"v": float("-inf")},
        {"v": [1, float("nan")]},
        {"a": {"b": [{"c": float("inf")}]}},
        {"v": {"k": object()}},
        {"v": [object()]},
        {1: "int key"},
        {b"k": "bytes key"},
        {None: "none key"},
        {("a",): "tuple key"},
        {"v": {1: "nested int key"}},
        {"v": [{2: "nested int key in list"}]},
    ],
)
def test_details_rejects_non_json_python_values(bad):
    with pytest.raises(ValidationError):
        _err(bad)


@pytest.mark.parametrize("bad", [[], [{"a": 1}], "text", 5, 1.5, True, b"{}"])
def test_details_must_be_an_object(bad):
    with pytest.raises(ValidationError):
        _err(bad)


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers_in_json_input_are_rejected_not_nulled(literal):
    raw = '{"code":"VALIDATION_ERROR","message":"m","details":{"a":' + literal + "}}"
    with pytest.raises(ValidationError):
        ErrorDetail.model_validate_json(raw)


def test_nested_structure_is_not_altered_by_validation_or_serialization():
    details = {"list": [1, 2.5, "x", None, {"k": [True, False]}], "n": 7}
    err = _err(details)
    assert err.details == details
    assert err.model_dump()["details"] == details
    assert json.loads(err.model_dump_json())["details"] == details
