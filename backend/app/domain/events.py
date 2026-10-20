from typing import Annotated, Literal

from pydantic import Field

from app.domain.base import ContractModel
from app.domain.enums import ErrorCode, EventType
from app.domain.types import NonEmptyStr, UtcDatetime, Uuid4


class StartedPayload(ContractModel):
    status: Literal["running"]


class CompletedPayload(ContractModel):
    status: Literal["completed"]


class ErrorSummary(ContractModel):
    """Safe, non-authoritative summary (DATA_CONTRACTS section 12); deliberately no `details`."""

    code: ErrorCode
    message: NonEmptyStr


class FailedPayload(ContractModel):
    status: Literal["failed"]
    error: ErrorSummary


class _EventEnvelope(ContractModel):
    event_id: Uuid4
    occurred_at: UtcDatetime
    analysis_id: Uuid4


class AnalysisStartedEvent(_EventEnvelope):
    event_type: Literal[EventType.ANALYSIS_STARTED]
    payload: StartedPayload


class AnalysisCompletedEvent(_EventEnvelope):
    event_type: Literal[EventType.ANALYSIS_COMPLETED]
    payload: CompletedPayload


class AnalysisFailedEvent(_EventEnvelope):
    event_type: Literal[EventType.ANALYSIS_FAILED]
    payload: FailedPayload


# Validate with pydantic.TypeAdapter(WebSocketEvent).
WebSocketEvent = Annotated[
    AnalysisStartedEvent | AnalysisCompletedEvent | AnalysisFailedEvent,
    Field(discriminator="event_type"),
]
