import json
import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from app.domain.types import (
    DecimalString,
    NonNegativeDecimalString,
    PositiveDecimalString,
    SemVer,
    UtcDatetime,
    Uuid4,
)


@pytest.mark.parametrize("value", ["0", "0.0", "1", "10", "3642.15", "0.000001", "100.50"])
def test_decimal_string_valid(value):
    assert TypeAdapter(DecimalString).validate_python(value) == value


@pytest.mark.parametrize(
    "value",
    ["", " 1", "1 ", "01", "00", "-1", "+1", ".5", "5.", "1e3", "1E3", "1,5", "12\n", "1.2.3", "NaN", "Infinity"],
)
def test_decimal_string_invalid_formats(value):
    with pytest.raises(ValidationError):
        TypeAdapter(DecimalString).validate_python(value)


@pytest.mark.parametrize("value", ["١٢", "1٢", "１"])
def test_decimal_string_rejects_non_ascii_digits(value):
    with pytest.raises(ValidationError):
        TypeAdapter(DecimalString).validate_python(value)


@pytest.mark.parametrize("value", [1, 1.5, 3642.15, None, True, b"1"])
def test_decimal_string_rejects_non_strings(value):
    with pytest.raises(ValidationError):
        TypeAdapter(DecimalString).validate_python(value)


@pytest.mark.parametrize("value", ["0", "0.0", "0.000"])
def test_positive_rejects_zero(value):
    with pytest.raises(ValidationError):
        TypeAdapter(PositiveDecimalString).validate_python(value)


@pytest.mark.parametrize("value", ["0.000001", "1", "3642.15"])
def test_positive_accepts_positive(value):
    assert TypeAdapter(PositiveDecimalString).validate_python(value) == value


@pytest.mark.parametrize("value", ["0", "0.00", "5"])
def test_non_negative_accepts_zero(value):
    assert TypeAdapter(NonNegativeDecimalString).validate_python(value) == value


def test_non_negative_rejects_negative():
    with pytest.raises(ValidationError):
        TypeAdapter(NonNegativeDecimalString).validate_python("-0.1")


@pytest.mark.parametrize("value", ["2026-09-18T14:30:00Z", "2026-09-18T14:30:00+00:00"])
def test_utc_accepts_zero_offset(value):
    parsed = TypeAdapter(UtcDatetime).validate_python(value)
    assert parsed.utcoffset() == timedelta(0)


@pytest.mark.parametrize("value", ["2026-09-18T14:30:00", "2026-09-18T16:30:00+02:00", "2026-09-18T09:30:00-05:00"])
def test_utc_rejects_naive_and_non_utc(value):
    with pytest.raises(ValidationError):
        TypeAdapter(UtcDatetime).validate_python(value)


def test_utc_rejects_naive_and_non_utc_datetime_objects():
    adapter = TypeAdapter(UtcDatetime)
    with pytest.raises(ValidationError):
        adapter.validate_python(datetime(2026, 9, 18, 14, 30))
    with pytest.raises(ValidationError):
        adapter.validate_python(datetime(2026, 9, 18, 14, 30, tzinfo=timezone(timedelta(hours=1))))


def test_utc_serializes_with_z_suffix():
    adapter = TypeAdapter(UtcDatetime)
    stamp = datetime(2026, 9, 18, 14, 30, tzinfo=UTC)
    assert adapter.dump_json(stamp) == b'"2026-09-18T14:30:00Z"'
    assert adapter.dump_python(stamp, mode="json") == "2026-09-18T14:30:00Z"


UUID_LOWER = "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e"
UUID_UPPER = UUID_LOWER.upper()


def test_uuid4_accepts_v4_only():
    adapter = TypeAdapter(Uuid4)
    adapter.validate_python(UUID_LOWER)
    for bad in ["7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e", "not-a-uuid", "", 5]:
        with pytest.raises(ValidationError):
            adapter.validate_python(bad)


@pytest.mark.parametrize("value", [UUID_LOWER, UUID_UPPER, "7C2e1EF6-1c88-4A3a-87F5-f3d5c9a0f11E"])
def test_uuid4_accepts_canonical_hyphenated_any_hex_case(value):
    adapter = TypeAdapter(Uuid4)
    expected = uuid.UUID(UUID_LOWER)
    assert adapter.validate_python(value) == expected
    assert adapter.validate_json(json.dumps(value)) == expected


@pytest.mark.parametrize(
    "value",
    [
        "7c2e1ef61c884a3a87f5f3d5c9a0f11e",  # no hyphens
        "{7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e}",  # braces
        "urn:uuid:7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",  # URN prefix
        " 7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e",
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e ",
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e\n",  # trailing newline
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11",  # too short
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11ee",  # too long
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11g",  # non-hex
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11٥",  # non-ASCII digit
        "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11-",
        "7c2e1ef6_1c88_4a3a_87f5_f3d5c9a0f11e",
    ],
)
def test_uuid4_rejects_non_canonical_strings(value):
    adapter = TypeAdapter(Uuid4)
    with pytest.raises(ValidationError):
        adapter.validate_python(value)
    with pytest.raises(ValidationError):
        adapter.validate_json(json.dumps(value))


@pytest.mark.parametrize(
    "value",
    [
        "7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e",  # version 1
        "7c2e1ef6-1c88-5a3a-87f5-f3d5c9a0f11e",  # version 5
        "7c2e1ef6-1c88-4a3a-c7f5-f3d5c9a0f11e",  # variant 0b11 (not RFC 4122)
        "7c2e1ef6-1c88-4a3a-37f5-f3d5c9a0f11e",  # variant 0b00
    ],
)
def test_uuid4_rejects_wrong_version_or_variant(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Uuid4).validate_python(value)


def test_uuid4_accepts_uuid_objects_only_when_v4():
    adapter = TypeAdapter(Uuid4)
    valid = uuid.UUID(UUID_LOWER)
    assert adapter.validate_python(valid) == valid
    with pytest.raises(ValidationError):
        adapter.validate_python(uuid.UUID("7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e"))


@pytest.mark.parametrize(
    "value",
    [None, 5, 1.5, True, UUID_LOWER.encode(), uuid.UUID(UUID_LOWER).bytes, uuid.UUID(UUID_LOWER).int, [UUID_LOWER], {}],
)
def test_uuid4_rejects_other_input_types(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Uuid4).validate_python(value)


@pytest.mark.parametrize("raw", ["5", "null", "true", "[]", "{}"])
def test_uuid4_json_rejects_non_string_values(raw):
    with pytest.raises(ValidationError):
        TypeAdapter(Uuid4).validate_json(raw)


def test_uuid4_serializes_canonical_lowercase():
    adapter = TypeAdapter(Uuid4)
    parsed = adapter.validate_python(UUID_UPPER)
    assert adapter.dump_python(parsed, mode="json") == UUID_LOWER
    assert adapter.dump_json(parsed) == f'"{UUID_LOWER}"'.encode()


@pytest.mark.parametrize("value", ["1.0.0", "0.0.0", "1.1.0", "2.0.0", "10.20.30"])
def test_semver_valid(value):
    assert TypeAdapter(SemVer).validate_python(value) == value


@pytest.mark.parametrize("value", ["", "1", "1.0", "01.0.0", "1.00.0", "1.0.0-beta", "v1.0.0", "1.0.0.0", "1.0.0\n", 1])
def test_semver_invalid(value):
    with pytest.raises(ValidationError):
        TypeAdapter(SemVer).validate_python(value)
