import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import AnalysisStatus, DataSourceMode, Instrument, Timeframe
from app.persistence.base import Base

# Columns whose presence defines the lifecycle (DATA_CONTRACTS §11).
_LIFECYCLE_COLUMNS = frozenset(
    {"started_at_utc", "completed_at_utc", "failed_at_utc", "error", "analysis", "failure_snapshot"}
)


def _in_list(column: str, values: type[StrEnum]) -> str:
    return f"{column} IN ({', '.join(repr(m.value) for m in values)})"


def _lifecycle_check() -> str:
    # Every branch only tests IS [NOT] NULL, which is never NULL itself, so a missing value cannot
    # slip through the way a bare comparison would.
    def branch(status: AnalysisStatus, present: set[str], unconstrained: set[str] = frozenset()) -> str:
        absent = _LIFECYCLE_COLUMNS - present - unconstrained
        parts = [f"status = '{status.value}'"]
        parts += [f"{c} IS NOT NULL" for c in sorted(present)]
        parts += [f"{c} IS NULL" for c in sorted(absent)]
        return "(" + " AND ".join(parts) + ")"

    return " OR ".join(
        [
            branch(AnalysisStatus.PENDING, set()),
            branch(AnalysisStatus.RUNNING, {"started_at_utc"}),
            branch(AnalysisStatus.COMPLETED, {"started_at_utc", "completed_at_utc", "analysis"}),
            # A failed run may or may not carry a failure snapshot (decision D1).
            branch(
                AnalysisStatus.FAILED,
                {"started_at_utc", "failed_at_utc", "error"},
                unconstrained={"failure_snapshot"},
            ),
        ]
    )


class AnalysisRunRow(Base):
    """Persistence shape of an AnalysisRun. Never leaks into the domain models."""

    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(_in_list("status", AnalysisStatus), name="status_valid"),
        CheckConstraint(_in_list("symbol", Instrument), name="symbol_valid"),
        CheckConstraint(_in_list("timeframe", Timeframe), name="timeframe_valid"),
        CheckConstraint(_in_list("data_mode", DataSourceMode), name="data_mode_valid"),
        CheckConstraint(_lifecycle_check(), name="lifecycle"),
        CheckConstraint(
            "started_at_utc IS NULL OR started_at_utc >= created_at_utc", name="started_after_created"
        ),
        CheckConstraint(
            "completed_at_utc IS NULL OR "
            "(started_at_utc IS NOT NULL AND completed_at_utc >= started_at_utc)",
            name="completed_after_started",
        ),
        CheckConstraint(
            "failed_at_utc IS NULL OR "
            "(started_at_utc IS NOT NULL AND failed_at_utc >= started_at_utc)",
            name="failed_after_started",
        ),
        CheckConstraint("error IS NULL OR jsonb_typeof(error) = 'object'", name="error_is_object"),
        CheckConstraint(
            "analysis IS NULL OR jsonb_typeof(analysis) = 'object'", name="analysis_is_object"
        ),
        CheckConstraint(
            "failure_snapshot IS NULL OR jsonb_typeof(failure_snapshot) = 'object'",
            name="failure_snapshot_is_object",
        ),
        CheckConstraint(
            "failure_snapshot IS NULL OR status = 'failed'", name="failure_snapshot_only_failed"
        ),
        # coalesce: a missing or null analysis_id in the JSON must fail, not evaluate to NULL.
        CheckConstraint(
            "analysis IS NULL OR coalesce((analysis ->> 'analysis_id') = analysis_id::text, false)",
            name="analysis_id_matches_row",
        ),
        Index("ix_analysis_runs_history", text("created_at_utc DESC"), text("analysis_id DESC")),
        Index("ix_analysis_runs_request_id", "request_id"),
    )

    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16))
    symbol: Mapped[str] = mapped_column(String(16))
    timeframe: Mapped[str] = mapped_column(String(16))
    data_mode: Mapped[str] = mapped_column(String(16))
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # none_as_null: Python None must be SQL NULL, not the JSON value `null`, or the lifecycle CHECK
    # (which tests IS NULL) would reject every pending/running row.
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    failure_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
