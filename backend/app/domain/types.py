import math
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    UUID4,
    AfterValidator,
    AwareDatetime,
    BeforeValidator,
    JsonValue,
    Strict,
    StringConstraints,
)

# DATA_CONTRACTS §3.5, with ASCII digits and full-string matching (no trailing newline).
_DECIMAL_PATTERN = r"^(0|[1-9][0-9]*)(\.[0-9]+)?$"
# DATA_CONTRACTS §17: MAJOR.MINOR.PATCH.
_SEMVER_PATTERN = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
# RFC 3339 section 5.6 date-time (DATA_CONTRACTS §3.3): full-date, "T", full-time with seconds and
# an offset. RFC 3339 ABNF literals are case-insensitive, so "t"/"z" are valid; a space is not in the
# grammar. Fractional digits are accepted at any length (see UtcDatetime).
_RFC3339 = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?([Zz]|[+-][0-9]{2}:[0-9]{2})"
)
_UUID_TEXT = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _positive(value: str) -> str:
    if Decimal(value) <= 0:
        raise ValueError("value must be strictly positive")
    return value


def _utc_input(value: Any) -> Any:
    # Runs before AwareDatetime so numbers, numeric strings and loose formats are never coerced.
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and _RFC3339.fullmatch(value):
        return value
    raise ValueError("timestamp must be a datetime or an RFC 3339 string with seconds and a Z or +hh:mm offset")


def _uuid_input(value: Any) -> Any:
    # Runs before UUID4 so pydantic never normalizes compact, braced, URN, padded or bytes input.
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and _UUID_TEXT.fullmatch(value):
        return value
    raise ValueError("identifier must be a UUID v4 in the canonical 8-4-4-4-12 hyphenated format")


def _utc(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC (offset 0)")
    return value


def _finite_json(value: Any) -> Any:
    # JSON has no NaN/Infinity; pydantic would otherwise serialize them silently as null.
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("JSON numbers must be finite")
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return value


DecimalString = Annotated[str, StringConstraints(strict=True, pattern=_DECIMAL_PATTERN)]
PositiveDecimalString = Annotated[DecimalString, AfterValidator(_positive)]
NonNegativeDecimalString = DecimalString  # the pattern already excludes negatives

# Python datetimes or RFC 3339 strings only. Known limit: `datetime` holds microseconds, and pydantic
# truncates (does not round) any finer fractional digits; leap seconds (":60") are rejected.
UtcDatetime = Annotated[AwareDatetime, BeforeValidator(_utc_input), AfterValidator(_utc)]
# Canonical 8-4-4-4-12 hyphenated form (DATA_CONTRACTS §3.2); upper- or lower-case ASCII hex input is
# accepted and always serialized in lower case. Version and variant are checked by UUID4.
Uuid4 = Annotated[UUID4, BeforeValidator(_uuid_input)]
SemVer = Annotated[str, StringConstraints(strict=True, pattern=_SEMVER_PATTERN)]
NonEmptyStr = Annotated[str, StringConstraints(strict=True, min_length=1)]
# A JSON object: string keys, recursive JSON values (str, int, finite float, bool, null, list, object).
JsonObject = Annotated[dict[Annotated[str, Strict()], JsonValue], AfterValidator(_finite_json)]
