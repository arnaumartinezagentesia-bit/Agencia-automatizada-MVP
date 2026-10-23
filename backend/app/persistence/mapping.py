from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from pydantic import ValidationError

from app.domain.market import MarketSnapshot
from app.domain.run import AnalysisRun, AnalysisSummary
from app.persistence.errors import CorruptRowError

_MAX_REPORTED_ERRORS = 5


class RunRow(Protocol):
    """The columns of analysis_runs, as exposed by a SQLAlchemy row or any attribute holder."""

    analysis_id: UUID
    request_id: UUID
    status: str
    symbol: str
    timeframe: str
    data_mode: str
    created_at_utc: datetime
    started_at_utc: datetime | None
    completed_at_utc: datetime | None
    failed_at_utc: datetime | None
    error: Any
    analysis: Any
    failure_snapshot: Any


def run_to_values(run: AnalysisRun, failure_snapshot: MarketSnapshot | None = None) -> dict[str, Any]:
    """Column values for a run. JSON payloads use the contract's JSON form (decimals stay strings)."""
    return {
        "analysis_id": run.analysis_id,
        "request_id": run.request_id,
        "status": run.status.value,
        "symbol": run.request.symbol.value,
        "timeframe": run.request.timeframe.value,
        "data_mode": run.request.data_mode.value,
        "created_at_utc": run.created_at_utc,
        "started_at_utc": run.started_at_utc,
        "completed_at_utc": run.completed_at_utc,
        "failed_at_utc": run.failed_at_utc,
        "error": run.error.model_dump(mode="json") if run.error is not None else None,
        "analysis": run.analysis.model_dump(mode="json") if run.analysis is not None else None,
        "failure_snapshot": (
            failure_snapshot.model_dump(mode="json") if failure_snapshot is not None else None
        ),
    }


def _as_utc(value: datetime | None) -> datetime | None:
    # Naive values are passed through so the domain's AwareDatetime check rejects them.
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(UTC)


def _describe(exc: ValidationError) -> str:
    errors = exc.errors(include_input=False, include_url=False, include_context=False)
    shown = [f"{'.'.join(str(p) for p in e['loc']) or '<root>'}: {e['type']}" for e in errors]
    return "; ".join(shown[:_MAX_REPORTED_ERRORS])


def row_to_run(row: RunRow) -> AnalysisRun:
    """Rebuild a validated AnalysisRun; anything inconsistent is a CorruptRowError, never a guess."""
    try:
        return AnalysisRun.model_validate(
            {
                "analysis_id": row.analysis_id,
                "status": row.status,
                "created_at_utc": _as_utc(row.created_at_utc),
                "started_at_utc": _as_utc(row.started_at_utc),
                "completed_at_utc": _as_utc(row.completed_at_utc),
                "failed_at_utc": _as_utc(row.failed_at_utc),
                "request_id": row.request_id,
                "request": {
                    "symbol": row.symbol,
                    "timeframe": row.timeframe,
                    "data_mode": row.data_mode,
                },
                "error": row.error,
                "analysis": row.analysis,
            }
        )
    except ValidationError as exc:
        reason = _describe(exc)
    # Raised outside the handler so the ValidationError (which holds the input) is not kept as
    # context. The internal failure_snapshot is validated only by row_to_failure_snapshot: a damaged
    # diagnostic blob must not make the public run unreadable.
    raise CorruptRowError(row.analysis_id, reason)


def row_to_failure_snapshot(row: RunRow) -> MarketSnapshot | None:
    if row.failure_snapshot is None:
        return None
    try:
        return MarketSnapshot.model_validate(row.failure_snapshot)
    except ValidationError as exc:
        reason = _describe(exc)
    raise CorruptRowError(row.analysis_id, reason)


class SummaryRow(Protocol):
    analysis_id: UUID
    symbol: str
    timeframe: str
    status: str
    created_at_utc: datetime
    data_mode: str


def row_to_summary(row: SummaryRow) -> AnalysisSummary:
    """History entry built from relational columns only (DATA_CONTRACTS §14.8)."""
    try:
        return AnalysisSummary.model_validate(
            {
                "analysis_id": row.analysis_id,
                "symbol": row.symbol,
                "timeframe": row.timeframe,
                "status": row.status,
                "timestamp_utc": _as_utc(row.created_at_utc),
                "data_source_mode": row.data_mode,
            }
        )
    except ValidationError as exc:
        reason = _describe(exc)
    raise CorruptRowError(row.analysis_id, reason)
