from enum import StrEnum


class Instrument(StrEnum):
    XAUUSD = "XAUUSD"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSourceMode(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"


class EventType(StrEnum):
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    LLM_ERROR = "LLM_ERROR"
    ANALYSIS_VALIDATION_ERROR = "ANALYSIS_VALIDATION_ERROR"
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class TrendDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    UNCLEAR = "unclear"


class TrendStrength(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    UNCLEAR = "unclear"


class VolatilityRegime(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNCLEAR = "unclear"


class KeyLevelType(StrEnum):
    SUPPORT = "support"
    RESISTANCE = "resistance"
