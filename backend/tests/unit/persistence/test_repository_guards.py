from datetime import timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.domain.market import MarketSnapshot
from app.domain.run import AnalysisRun
from app.persistence.errors import RunValidationError
from app.persistence.repository import (
    AnalysisRunRepository,
    _check_snapshot_matches_request,
    _check_timeline,
)


def _run(make, status):
    return AnalysisRun.model_validate(make.run(status))


def test_create_pending_revalidates_instances_built_without_validation(make):
    invalid = AnalysisRun.model_construct(**{**_run(make, "pending").__dict__, "analysis_id": "not-a-uuid"})
    repo = AnalysisRunRepository(sessionmaker())  # never reaches the database

    # Dumping a model built without validation makes pydantic warn before validation rejects it.
    with pytest.warns(UserWarning), pytest.raises(RunValidationError):
        repo.create_pending(invalid)


def test_timeline_accepts_ordered_timestamps(make):
    _check_timeline(_run(make, "completed"))


def test_timeline_rejects_start_before_creation(make):
    run = _run(make, "running")
    early = run.model_copy(update={"started_at_utc": run.created_at_utc - timedelta(seconds=1)})

    with pytest.raises(RunValidationError, match="started_at_utc"):
        _check_timeline(early)


def test_timeline_rejects_end_before_start(make):
    run = _run(make, "failed")
    early = run.model_copy(update={"failed_at_utc": run.started_at_utc - timedelta(seconds=1)})

    with pytest.raises(RunValidationError, match="failed_at_utc"):
        _check_timeline(early)


def test_snapshot_must_match_the_request(make):
    run = _run(make, "failed")
    ok = MarketSnapshot.model_validate(make.snapshot())
    _check_snapshot_matches_request(run, ok)
    _check_snapshot_matches_request(run, None)

    live = make.snapshot()
    live["data_source"]["mode"] = "live"
    other_timeframe = make.snapshot()
    other_timeframe["timeframe"] = "4h"
    for payload in (live, other_timeframe):
        with pytest.raises(RunValidationError):
            _check_snapshot_matches_request(run, MarketSnapshot.model_validate(payload))
