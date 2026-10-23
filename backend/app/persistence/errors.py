from uuid import UUID

from app.domain.enums import ErrorCode


class PersistenceError(Exception):
    """Base for every error raised by the persistence layer.

    Messages never carry connection URLs, credentials or row payloads.
    """

    error_code = ErrorCode.PERSISTENCE_ERROR


class PersistenceConfigurationError(PersistenceError):
    """The database configuration is missing or unusable."""

    error_code = ErrorCode.CONFIGURATION_ERROR


class RunNotFoundError(PersistenceError):
    error_code = ErrorCode.NOT_FOUND

    def __init__(self, analysis_id: UUID) -> None:
        super().__init__(f"analysis run {analysis_id} was not found")
        self.analysis_id = analysis_id


class IllegalTransitionError(PersistenceError):
    """The run is not in the state the requested operation requires."""


class RunValidationError(PersistenceError):
    """The data supplied for a transition does not form a valid AnalysisRun."""


class CorruptRowError(PersistenceError):
    """A stored row does not reconstruct into a valid domain object."""

    def __init__(self, analysis_id: UUID | None, reason: str) -> None:
        super().__init__(f"stored analysis run {analysis_id} is inconsistent: {reason}")
        self.analysis_id = analysis_id
