import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import insert, text

from app.domain.enums import AnalysisStatus, DataSourceMode
from app.domain.errors import ErrorDetail
from app.domain.market import MarketSnapshot
from app.persistence.errors import (
    CorruptRowError,
    IllegalTransitionError,
    PersistenceError,
    RunNotFoundError,
    RunValidationError,
)
from tests.integration.conftest import TABLE, new_analysis, new_pending, raw_row

STARTED = datetime(2026, 9, 18, 14, 30, 0, tzinfo=timezone.utc)
ERROR = ErrorDetail(code="PROVIDER_ERROR", message="Market data provider failed.")


@pytest.fixture
def pending(repo, make):
    return repo.create_pending(new_pending(make))


@pytest.fixture
def running(repo, pending):
    return repo.mark_running(pending.analysis_id, STARTED)


def test_pending_run_round_trips(repo, pending):
    assert repo.get(pending.analysis_id) == pending
    assert pending.status is AnalysisStatus.PENDING


def test_running_run_round_trips(repo, running):
    assert repo.get(running.analysis_id) == running
    assert running.started_at_utc == STARTED


def test_completed_run_round_trips_with_the_full_analysis(repo, make, running):
    analysis = new_analysis(make, running.analysis_id)

    completed = repo.mark_completed(running.analysis_id, analysis)

    stored = repo.get(running.analysis_id)
    assert stored == completed
    assert stored.analysis == analysis
    assert stored.completed_at_utc == analysis.timestamp_utc
    assert stored.error is None and stored.failed_at_utc is None


def test_failed_run_round_trips_without_analysis_or_model_metadata(db, repo, running):
    failed = repo.mark_failed(running.analysis_id, STARTED + timedelta(seconds=3), ERROR)

    assert repo.get(running.analysis_id) == failed
    assert failed.analysis is None and failed.error == ERROR
    row = raw_row(db, running.analysis_id)
    assert row["analysis"] is None and row["failure_snapshot"] is None
    assert "model_metadata" not in str(row["error"])


def test_failed_run_keeps_a_validated_failure_snapshot_internally(repo, make, running):
    snapshot = MarketSnapshot.model_validate(make.snapshot())

    failed = repo.mark_failed(running.analysis_id, STARTED, ERROR, snapshot)

    assert repo.get_failure_snapshot(running.analysis_id) == snapshot
    assert not hasattr(failed, "failure_snapshot")
    assert "failure_snapshot" not in failed.model_dump()


def test_failure_snapshot_is_null_when_not_given(repo, running):
    repo.mark_failed(running.analysis_id, STARTED, ERROR)

    assert repo.get_failure_snapshot(running.analysis_id) is None


@pytest.mark.parametrize("mode", ["fixture", "live"])
def test_data_provenance_is_preserved_end_to_end(repo, make, mode):
    run = repo.create_pending(new_pending(make, mode=mode))
    repo.mark_running(run.analysis_id, STARTED)

    repo.mark_completed(run.analysis_id, new_analysis(make, run.analysis_id, mode=mode))

    stored = repo.get(run.analysis_id)
    assert stored.request.data_mode is DataSourceMode(mode)
    assert stored.analysis.market_snapshot.data_source.mode is DataSourceMode(mode)
    assert [s.mode for s in stored.analysis.data_sources] == [DataSourceMode(mode)]
    assert repo.list_summaries(limit=1)[0].data_source_mode is DataSourceMode(mode)


def test_provenance_that_contradicts_the_request_is_refused_without_mutation(db, repo, make, running):
    before = raw_row(db, running.analysis_id)
    live_analysis = new_analysis(make, running.analysis_id, mode="live")  # request was fixture

    with pytest.raises(RunValidationError):
        repo.mark_completed(running.analysis_id, live_analysis)

    assert raw_row(db, running.analysis_id) == before


def test_analysis_of_another_run_is_refused_without_mutation(db, repo, make, running):
    before = raw_row(db, running.analysis_id)

    with pytest.raises(RunValidationError):
        repo.mark_completed(running.analysis_id, new_analysis(make, uuid.uuid4()))

    assert raw_row(db, running.analysis_id) == before


def test_a_start_before_creation_is_refused_without_mutation(db, repo, pending):
    before = raw_row(db, pending.analysis_id)

    with pytest.raises(RunValidationError, match="started_at_utc"):
        repo.mark_running(pending.analysis_id, pending.created_at_utc - timedelta(seconds=1))

    assert raw_row(db, pending.analysis_id) == before


def test_an_analysis_dated_before_the_start_is_refused_without_mutation(db, repo, make):
    run = repo.create_pending(new_pending(make))
    repo.mark_running(run.analysis_id, STARTED + timedelta(minutes=10))  # analysis is dated 14:30:05
    before = raw_row(db, run.analysis_id)

    with pytest.raises(RunValidationError, match="completed_at_utc"):
        repo.mark_completed(run.analysis_id, new_analysis(make, run.analysis_id))

    assert raw_row(db, run.analysis_id) == before


@pytest.mark.parametrize("field, value", [("timeframe", "4h"), ("mode", "live")])
def test_failure_snapshot_contradicting_the_request_is_refused(db, repo, make, running, field, value):
    payload = make.snapshot()
    if field == "mode":
        payload["data_source"]["mode"] = value
    else:
        payload[field] = value
    before = raw_row(db, running.analysis_id)

    with pytest.raises(RunValidationError):
        repo.mark_failed(running.analysis_id, STARTED, ERROR, MarketSnapshot.model_validate(payload))

    assert raw_row(db, running.analysis_id) == before


def test_create_pending_rejects_runs_that_are_not_pending(repo, make):
    from app.domain.run import AnalysisRun

    with pytest.raises(IllegalTransitionError):
        repo.create_pending(AnalysisRun.model_validate(make.run("running")))


def test_creating_the_same_run_twice_is_a_persistence_error_without_driver_context(repo, pending):
    with pytest.raises(PersistenceError, match="pk_analysis_runs") as info:
        repo.create_pending(pending)

    # The driver error holds the statement and the row payload; it must not travel with the error.
    assert info.value.__cause__ is None and info.value.__context__ is None


def test_failure_snapshot_of_an_unknown_run_is_not_found(repo):
    with pytest.raises(RunNotFoundError):
        repo.get_failure_snapshot(uuid.uuid4())


# --- transitions -------------------------------------------------------------------------------

TARGETS = {
    "running": lambda repo, make, id_: repo.mark_running(id_, STARTED),
    "completed": lambda repo, make, id_: repo.mark_completed(id_, new_analysis(make, id_)),
    "failed": lambda repo, make, id_: repo.mark_failed(id_, STARTED, ERROR),
}
LEGAL = {"pending": {"running"}, "running": {"completed", "failed"}, "completed": set(), "failed": set()}


def _advance(repo, make, run, to):
    id_ = run.analysis_id
    if to in ("running", "completed", "failed"):
        repo.mark_running(id_, STARTED)
    if to == "completed":
        repo.mark_completed(id_, new_analysis(make, id_))
    if to == "failed":
        repo.mark_failed(id_, STARTED, ERROR)


@pytest.mark.parametrize("current", ["pending", "running", "completed", "failed"])
@pytest.mark.parametrize("target", ["running", "completed", "failed"])
def test_every_transition_is_either_legal_or_refused_without_side_effects(
    db, repo, make, current, target
):
    run = repo.create_pending(new_pending(make))
    _advance(repo, make, run, current)
    before = raw_row(db, run.analysis_id)

    if target in LEGAL[current]:
        TARGETS[target](repo, make, run.analysis_id)
        assert repo.get(run.analysis_id).status.value == target
    else:
        with pytest.raises(IllegalTransitionError):
            TARGETS[target](repo, make, run.analysis_id)
        assert raw_row(db, run.analysis_id) == before


@pytest.mark.parametrize("target", ["running", "completed", "failed"])
def test_unknown_runs_are_reported_as_not_found(repo, make, target):
    unknown = uuid.uuid4()

    with pytest.raises(RunNotFoundError):
        TARGETS[target](repo, make, unknown)
    with pytest.raises(RunNotFoundError):
        repo.get(unknown)


def test_a_failure_before_the_start_is_refused_without_mutation(db, repo, running):
    before = raw_row(db, running.analysis_id)

    with pytest.raises(RunValidationError, match="failed_at_utc"):
        repo.mark_failed(running.analysis_id, STARTED - timedelta(seconds=1), ERROR)

    assert raw_row(db, running.analysis_id) == before


# --- transactions ------------------------------------------------------------------------------


def test_completed_result_is_invisible_to_other_readers_until_commit(session_factory, repo, make, running):
    analysis = new_analysis(make, running.analysis_id)
    writer, reader = session_factory(), session_factory()
    try:
        repo.mark_completed(running.analysis_id, analysis, session=writer)

        assert repo.get(running.analysis_id, session=reader).status is AnalysisStatus.RUNNING
        assert repo.get(running.analysis_id, session=reader).analysis is None
        reader.rollback()

        writer.commit()

        seen = repo.get(running.analysis_id, session=reader)
        assert seen.status is AnalysisStatus.COMPLETED and seen.analysis == analysis
    finally:
        writer.close()
        reader.close()


def test_failed_result_is_invisible_until_commit(session_factory, repo, running):
    writer, reader = session_factory(), session_factory()
    try:
        repo.mark_failed(running.analysis_id, STARTED, ERROR, session=writer)

        assert repo.get(running.analysis_id, session=reader).status is AnalysisStatus.RUNNING
        reader.rollback()
        writer.commit()
        assert repo.get(running.analysis_id, session=reader).status is AnalysisStatus.FAILED
    finally:
        writer.close()
        reader.close()


def test_rolled_back_completion_leaves_the_run_running(session_factory, repo, make, running):
    writer = session_factory()
    try:
        repo.mark_completed(running.analysis_id, new_analysis(make, running.analysis_id), session=writer)
        writer.rollback()
    finally:
        writer.close()

    assert repo.get(running.analysis_id).status is AnalysisStatus.RUNNING


def test_pending_to_running_commits_on_its_own(session_factory, repo, pending):
    repo.mark_running(pending.analysis_id, STARTED)

    other = session_factory()
    try:
        assert repo.get(pending.analysis_id, session=other).status is AnalysisStatus.RUNNING
    finally:
        other.close()


def test_competing_terminal_transitions_cannot_both_win(session_factory, repo, make, running):
    analysis = new_analysis(make, running.analysis_id)
    first = session_factory()
    outcome: dict[str, object] = {}

    def competitor():
        try:
            outcome["result"] = repo.mark_failed(running.analysis_id, STARTED, ERROR)
        except Exception as exc:  # noqa: BLE001 - recorded and asserted below
            outcome["error"] = exc

    try:
        repo.mark_completed(running.analysis_id, analysis, session=first)  # holds the row lock
        thread = threading.Thread(target=competitor)
        thread.start()
        thread.join(timeout=1)
        assert thread.is_alive(), "the competing transition should be waiting on the row lock"
        first.commit()
        thread.join(timeout=10)
        assert not thread.is_alive()
    finally:
        first.close()

    assert isinstance(outcome.get("error"), IllegalTransitionError)
    assert repo.get(running.analysis_id).status is AnalysisStatus.COMPLETED


# --- corrupt rows ------------------------------------------------------------------------------


def _insert_raw(db, **overrides):
    analysis_id = overrides.pop("analysis_id", uuid.uuid4())
    row = {
        "analysis_id": analysis_id,
        "request_id": uuid.uuid4(),
        "status": "completed",
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "data_mode": "fixture",
        "created_at_utc": STARTED,
        "started_at_utc": STARTED,
        "completed_at_utc": STARTED + timedelta(seconds=5),
        "failed_at_utc": None,
        "error": None,
        "analysis": {"analysis_id": str(analysis_id)},
        **overrides,
    }
    with db.begin() as connection:
        connection.execute(insert(TABLE).values(**row))
    return analysis_id


def test_a_row_that_satisfies_postgres_but_not_the_domain_is_reported_as_corrupt(db, repo):
    analysis_id = _insert_raw(db)  # analysis JSON is just {"analysis_id": ...}

    with pytest.raises(CorruptRowError) as info:
        repo.get(analysis_id)

    assert str(analysis_id) in str(info.value)


def test_a_row_whose_requested_mode_contradicts_the_stored_analysis_is_corrupt(db, repo, make):
    analysis_id = uuid.uuid4()
    analysis = new_analysis(make, analysis_id).model_dump(mode="json")
    _insert_raw(
        db,
        analysis_id=analysis_id,
        analysis=analysis,
        data_mode="live",
        completed_at_utc=datetime(2026, 9, 18, 14, 30, 5, tzinfo=timezone.utc),
    )

    with pytest.raises(CorruptRowError):
        repo.get(analysis_id)


def test_a_transition_on_a_corrupt_row_is_refused(db, repo):
    analysis_id = _insert_raw(db)

    with pytest.raises(CorruptRowError):
        repo.mark_failed(analysis_id, STARTED, ERROR)


def test_a_corrupt_failure_snapshot_is_reported_without_hiding_the_run(db, repo):
    analysis_id = _insert_raw(
        db,
        status="failed",
        completed_at_utc=None,
        failed_at_utc=STARTED,
        analysis=None,
        error={"code": "PROVIDER_ERROR", "message": "x"},
        failure_snapshot={"symbol": "XAUUSD"},
    )

    assert repo.get(analysis_id).status is AnalysisStatus.FAILED
    with pytest.raises(CorruptRowError):
        repo.get_failure_snapshot(analysis_id)


# --- history -----------------------------------------------------------------------------------


def _ids(summaries):
    return [s.analysis_id for s in summaries]


def test_history_is_ordered_by_creation_time_then_id_descending(repo, make):
    t = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    same_time = [uuid.UUID(f"00000000-0000-4000-8000-00000000000{n}") for n in (1, 3, 2)]
    stamp = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    oldest = repo.create_pending(new_pending(make, created=stamp(t - timedelta(hours=1))))
    newest = repo.create_pending(new_pending(make, created=stamp(t + timedelta(hours=1))))
    tied = [repo.create_pending(new_pending(make, analysis_id=i, created=stamp(t))) for i in same_time]

    ordered = _ids(repo.list_summaries(limit=10))

    expected_tie = sorted((r.analysis_id for r in tied), reverse=True)
    assert ordered == [newest.analysis_id, *expected_tie, oldest.analysis_id]


def test_history_pagination_slices_the_same_order(repo, make):
    runs = [
        repo.create_pending(new_pending(make, created=f"2026-09-18T10:00:0{n}Z")) for n in range(5)
    ]
    newest_first = [r.analysis_id for r in reversed(runs)]

    assert _ids(repo.list_summaries(limit=2)) == newest_first[:2]
    assert _ids(repo.list_summaries(limit=2, offset=2)) == newest_first[2:4]
    assert _ids(repo.list_summaries(limit=2, offset=4)) == newest_first[4:]
    assert repo.list_summaries(limit=2, offset=5) == []


def test_history_summary_describes_the_run_as_requested(repo, make):
    run = repo.create_pending(new_pending(make, created="2026-09-18T10:00:00Z", mode="live"))
    repo.mark_running(run.analysis_id, STARTED)

    (summary,) = repo.list_summaries(limit=5)

    assert summary.analysis_id == run.analysis_id
    assert summary.status is AnalysisStatus.RUNNING
    assert summary.timestamp_utc == run.created_at_utc
    assert summary.data_source_mode is DataSourceMode.LIVE


def test_history_does_not_depend_on_json_columns(db, repo, make):
    # Corrupt payloads must not break (or reorder) the history, which uses relational columns only.
    good = repo.create_pending(new_pending(make, created="2026-09-18T10:00:00Z"))
    bad_id = _insert_raw(db, created_at_utc=datetime(2026, 9, 19, tzinfo=timezone.utc), completed_at_utc=datetime(2026, 9, 19, 0, 0, 5, tzinfo=timezone.utc), started_at_utc=datetime(2026, 9, 19, tzinfo=timezone.utc))

    assert _ids(repo.list_summaries(limit=10)) == [bad_id, good.analysis_id]


@pytest.mark.parametrize("limit, offset", [(0, 0), (-1, 0), (1, -1)])
def test_history_rejects_invalid_pagination(repo, limit, offset):
    with pytest.raises(ValueError):
        repo.list_summaries(limit=limit, offset=offset)


def test_request_id_lookup_is_served_by_a_non_unique_index(db):
    with db.connect() as connection:
        indexes = connection.execute(
            text("select indexdef from pg_indexes where indexname = 'ix_analysis_runs_request_id'")
        ).scalar_one()

    assert "UNIQUE" not in indexes
