import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.analysis import MarketAnalysis
from app.domain.enums import AnalysisStatus
from app.domain.errors import ErrorDetail
from app.domain.market import MarketSnapshot
from app.domain.run import AnalysisRun, AnalysisSummary
from app.persistence.errors import (
    IllegalTransitionError,
    PersistenceError,
    RunNotFoundError,
    RunValidationError,
)
from app.persistence.mapping import (
    row_to_failure_snapshot,
    row_to_run,
    row_to_summary,
    run_to_values,
)
from app.persistence.models import AnalysisRunRow

logger = logging.getLogger(__name__)

T = TypeVar("T")

_TABLE = AnalysisRunRow.__table__
# Columns a lifecycle transition may change; identity and request columns are immutable.
_MUTABLE_COLUMNS = (
    "status",
    "started_at_utc",
    "completed_at_utc",
    "failed_at_utc",
    "error",
    "analysis",
    "failure_snapshot",
)
_SUMMARY_COLUMNS = (
    _TABLE.c.analysis_id,
    _TABLE.c.symbol,
    _TABLE.c.timeframe,
    _TABLE.c.status,
    _TABLE.c.created_at_utc,
    _TABLE.c.data_mode,
)


class AnalysisRunRepository:
    """Lifecycle storage for AnalysisRun (DATA_CONTRACTS §11, ARCHITECTURE §23-24).

    Each operation opens, commits and closes its own transaction. Passing `session` instead makes the
    caller own the transaction: nothing is committed here, so a result stays invisible to other
    readers until the caller commits. After a PersistenceError on a caller-owned session the
    PostgreSQL transaction may be aborted: the caller must roll it back before reusing it.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_pending(self, run: AnalysisRun, *, session: Session | None = None) -> AnalysisRun:
        if run.status is not AnalysisStatus.PENDING:
            raise IllegalTransitionError("only a pending run can be created")
        try:
            run = AnalysisRun.model_validate(run.model_dump())
        except ValidationError:
            run = None
        if run is None:
            raise RunValidationError("run is not a valid AnalysisRun")

        def work(s: Session) -> None:
            s.execute(insert(_TABLE).values(**run_to_values(run)))

        self._run(session, work)
        return run

    def mark_running(
        self, analysis_id: UUID, started_at_utc: datetime, *, session: Session | None = None
    ) -> AnalysisRun:
        return self._transition(
            analysis_id,
            expected=AnalysisStatus.PENDING,
            changes={"status": AnalysisStatus.RUNNING, "started_at_utc": started_at_utc},
            session=session,
        )

    def mark_completed(
        self, analysis_id: UUID, analysis: MarketAnalysis, *, session: Session | None = None
    ) -> AnalysisRun:
        # DATA_CONTRACTS §11: MarketAnalysis.timestamp_utc is the run's completed_at_utc.
        return self._transition(
            analysis_id,
            expected=AnalysisStatus.RUNNING,
            changes={
                "status": AnalysisStatus.COMPLETED,
                "completed_at_utc": analysis.timestamp_utc,
                "analysis": analysis.model_dump(),
            },
            session=session,
        )

    def mark_failed(
        self,
        analysis_id: UUID,
        failed_at_utc: datetime,
        error: ErrorDetail,
        failure_snapshot: MarketSnapshot | None = None,
        *,
        session: Session | None = None,
    ) -> AnalysisRun:
        snapshot = self._revalidate_snapshot(failure_snapshot)
        return self._transition(
            analysis_id,
            expected=AnalysisStatus.RUNNING,
            changes={
                "status": AnalysisStatus.FAILED,
                "failed_at_utc": failed_at_utc,
                "error": error.model_dump(),
            },
            failure_snapshot=snapshot,
            session=session,
        )

    def get(self, analysis_id: UUID, *, session: Session | None = None) -> AnalysisRun:

        def work(s: Session) -> AnalysisRun:
            row = s.execute(select(_TABLE).where(_TABLE.c.analysis_id == analysis_id)).one_or_none()
            if row is None:
                raise RunNotFoundError(analysis_id)
            return row_to_run(row)

        return self._run(session, work)

    def get_failure_snapshot(
        self, analysis_id: UUID, *, session: Session | None = None
    ) -> MarketSnapshot | None:
        """Internal diagnostic data of a failed run; deliberately not part of AnalysisRun."""

        def work(s: Session) -> MarketSnapshot | None:
            row = s.execute(select(_TABLE).where(_TABLE.c.analysis_id == analysis_id)).one_or_none()
            if row is None:
                raise RunNotFoundError(analysis_id)
            return row_to_failure_snapshot(row)

        return self._run(session, work)

    def list_summaries(
        self, *, limit: int, offset: int = 0, session: Session | None = None
    ) -> list[AnalysisSummary]:
        if limit < 1 or offset < 0:
            raise ValueError("limit must be >= 1 and offset >= 0")
        query = (
            select(*_SUMMARY_COLUMNS)
            .order_by(_TABLE.c.created_at_utc.desc(), _TABLE.c.analysis_id.desc())
            .limit(limit)
            .offset(offset)
        )

        def work(s: Session) -> list[AnalysisSummary]:
            return [row_to_summary(row) for row in s.execute(query)]

        return self._run(session, work)

    @staticmethod
    def _revalidate_snapshot(snapshot: MarketSnapshot | None) -> MarketSnapshot | None:
        if snapshot is None:
            return None
        try:
            return MarketSnapshot.model_validate(snapshot.model_dump())
        except ValidationError:
            pass
        raise RunValidationError("failure_snapshot is not a valid MarketSnapshot")

    def _transition(
        self,
        analysis_id: UUID,
        *,
        expected: AnalysisStatus,
        changes: dict[str, Any],
        failure_snapshot: MarketSnapshot | None = None,
        session: Session | None,
    ) -> AnalysisRun:
        target = changes["status"]

        def work(s: Session) -> AnalysisRun:
            # The row lock serializes competing transitions on the same run.
            row = s.execute(
                select(_TABLE).where(_TABLE.c.analysis_id == analysis_id).with_for_update()
            ).one_or_none()
            if row is None:
                raise RunNotFoundError(analysis_id)
            current = row_to_run(row)
            if current.status is not expected:
                raise IllegalTransitionError(
                    f"cannot move a {current.status.value} run to {target.value}"
                )
            try:
                candidate = AnalysisRun.model_validate({**current.model_dump(), **changes})
            except ValidationError:
                candidate = None
            if candidate is None:
                raise RunValidationError(
                    f"data for the {target.value} transition is not a valid AnalysisRun"
                )
            _check_timeline(candidate)
            _check_snapshot_matches_request(candidate, failure_snapshot)

            values = run_to_values(candidate, failure_snapshot)
            result = s.execute(
                update(_TABLE)
                .where(_TABLE.c.analysis_id == analysis_id, _TABLE.c.status == expected.value)
                .values(**{column: values[column] for column in _MUTABLE_COLUMNS})
            )
            if result.rowcount != 1:
                raise IllegalTransitionError(f"{target.value} transition affected {result.rowcount} rows")
            return candidate

        return self._run(session, work)

    def _run(self, session: Session | None, work: Callable[[Session], T]) -> T:
        # A plain function, not a generator context manager: the translated error must be raised in a
        # frame with no exception being handled, or Python links the original driver/SQL exception
        # (statement, parameters, row payload, connection details) as its __context__. Only the
        # type, SQLSTATE and constraint name survive, and they are logged for the server side.
        failure: str | None = None
        try:
            if session is not None:
                return work(session)
            with self._session_factory() as own, own.begin():
                return work(own)
        except SQLAlchemyError as exc:
            orig = exc.orig if isinstance(exc, DBAPIError) else None
            constraint = getattr(getattr(orig, "diag", None), "constraint_name", None)
            logger.warning(
                "database operation failed: %s sqlstate=%s constraint=%s",
                type(exc).__name__,
                getattr(orig, "sqlstate", None),
                constraint,
            )
            if isinstance(exc, IntegrityError):
                failure = "database rejected the change" + (f" ({constraint})" if constraint else "")
            else:
                failure = f"database operation failed ({type(exc).__name__})"
        raise PersistenceError(failure)


def _check_timeline(run: AnalysisRun) -> None:
    """Pre-check of the temporal CHECKs, so callers get RunValidationError rather than a DB error."""
    started = run.started_at_utc
    if started is not None and started < run.created_at_utc:
        raise RunValidationError("started_at_utc precedes created_at_utc")
    for name, end in (("completed_at_utc", run.completed_at_utc), ("failed_at_utc", run.failed_at_utc)):
        if end is not None and started is not None and end < started:
            raise RunValidationError(f"{name} precedes started_at_utc")


def _check_snapshot_matches_request(run: AnalysisRun, snapshot: MarketSnapshot | None) -> None:
    # No silent fixture/live (or timeframe) substitution, also for diagnostic snapshots.
    if snapshot is None:
        return
    request = run.request
    if (
        snapshot.symbol != request.symbol
        or snapshot.timeframe != request.timeframe
        or snapshot.data_source.mode != request.data_mode
    ):
        raise RunValidationError("failure_snapshot does not match the run's request")
