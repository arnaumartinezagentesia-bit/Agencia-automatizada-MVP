import pytest

from app.domain import enums

EXPECTED = {
    "Instrument": ["XAUUSD"],
    "Timeframe": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "AnalysisStatus": ["pending", "running", "completed", "failed"],
    "DataSourceMode": ["fixture", "live"],
    "EventType": ["analysis.started", "analysis.completed", "analysis.failed"],
    "ErrorCode": [
        "VALIDATION_ERROR",
        "CONFIGURATION_ERROR",
        "PROVIDER_ERROR",
        "LLM_ERROR",
        "ANALYSIS_VALIDATION_ERROR",
        "PERSISTENCE_ERROR",
        "NOT_FOUND",
        "UNEXPECTED_ERROR",
    ],
    "TrendDirection": ["up", "down", "sideways", "unclear"],
    "TrendStrength": ["weak", "moderate", "strong", "unclear"],
    "VolatilityRegime": ["low", "moderate", "high", "unclear"],
    "KeyLevelType": ["support", "resistance"],
}


@pytest.mark.parametrize("name", EXPECTED)
def test_enum_values_match_contract_exactly(name):
    assert [m.value for m in getattr(enums, name)] == EXPECTED[name]


def test_no_unexpected_enums_defined():
    defined = {n for n, v in vars(enums).items() if isinstance(v, type) and issubclass(v, enums.StrEnum)}
    assert defined - {"StrEnum"} == set(EXPECTED)
