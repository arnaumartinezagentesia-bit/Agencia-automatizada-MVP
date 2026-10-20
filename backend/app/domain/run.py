from typing import Self

from pydantic import model_validator

from app.domain.analysis import MarketAnalysis
from app.domain.base import ContractModel
from app.domain.enums import AnalysisStatus, DataSourceMode, Instrument, Timeframe
from app.domain.errors import ErrorDetail
from app.domain.types import UtcDatetime, Uuid4


class AnalysisRequest(ContractModel):
    symbol: Instrument
    timeframe: Timeframe
    data_mode: DataSourceMode


class AnalysisRun(ContractModel):
    analysis_id: Uuid4
    status: AnalysisStatus
    created_at_utc: UtcDatetime
    started_at_utc: UtcDatetime | None = None
    completed_at_utc: UtcDatetime | None = None
    failed_at_utc: UtcDatetime | None = None
    request_id: Uuid4
    request: AnalysisRequest
    error: ErrorDetail | None = None
    analysis: MarketAnalysis | None = None

    @model_validator(mode="after")
    def _check_lifecycle(self) -> Self:
        # DATA_CONTRACTS §11. Flags: (started, completed, failed, analysis, error) is set.
        expected = {
            AnalysisStatus.PENDING: (False, False, False, False, False),
            AnalysisStatus.RUNNING: (True, False, False, False, False),
            AnalysisStatus.COMPLETED: (True, True, False, True, False),
            AnalysisStatus.FAILED: (True, False, True, False, True),
        }[self.status]
        actual = tuple(
            v is not None
            for v in (
                self.started_at_utc,
                self.completed_at_utc,
                self.failed_at_utc,
                self.analysis,
                self.error,
            )
        )
        if actual != expected:
            raise ValueError(f"fields are inconsistent with status={self.status.value}")

        if self.analysis is not None:
            a = self.analysis
            if a.timestamp_utc != self.completed_at_utc:
                raise ValueError("analysis.timestamp_utc must equal completed_at_utc")
            if a.analysis_id != self.analysis_id:
                raise ValueError("analysis.analysis_id must equal analysis_id")
            modes = [a.market_snapshot.data_source.mode, *(s.mode for s in a.data_sources)]
            if any(m != self.request.data_mode for m in modes):
                raise ValueError("request.data_mode must match the analysis data provenance")
        return self


class AnalysisSummary(ContractModel):
    analysis_id: Uuid4
    symbol: Instrument
    timeframe: Timeframe
    status: AnalysisStatus
    timestamp_utc: UtcDatetime
    data_source_mode: DataSourceMode
