import pytest
from pydantic import ValidationError

from app.domain.analysis import (
    KeyLevel,
    MarketAnalysis,
    ModelMetadata,
    TrendContext,
    VolatilityContext,
)
from app.domain.enums import TrendDirection, TrendStrength, VolatilityRegime


@pytest.mark.parametrize("direction", ["up", "down", "sideways", "unclear"])
@pytest.mark.parametrize("strength", ["weak", "moderate", "strong", "unclear"])
def test_trend_accepts_every_enum_combination(direction, strength):
    TrendContext(direction=direction, strength=strength, description="d")


def test_unclear_is_valid_not_an_error():
    t = TrendContext(direction="unclear", strength="unclear", description="Not enough evidence.")
    v = VolatilityContext(regime="unclear", description="Not enough evidence.")
    assert t.direction is TrendDirection.UNCLEAR and t.strength is TrendStrength.UNCLEAR
    assert v.regime is VolatilityRegime.UNCLEAR


@pytest.mark.parametrize(
    "payload",
    [
        {"direction": "bullish", "strength": "weak", "description": "d"},
        {"direction": "up", "strength": "huge", "description": "d"},
        {"direction": "up", "strength": "weak"},
        {"direction": "up", "strength": "weak", "description": "d", "action": "BUY"},
    ],
)
def test_invalid_trend(payload):
    with pytest.raises(ValidationError):
        TrendContext.model_validate(payload)


def test_invalid_volatility():
    for payload in [{"regime": "extreme", "description": "d"}, {"regime": "low"}]:
        with pytest.raises(ValidationError):
            VolatilityContext.model_validate(payload)


def test_description_limit_is_2000_everywhere():
    ok, too_long = "x" * 2000, "x" * 2001
    TrendContext(direction="up", strength="weak", description=ok)
    VolatilityContext(regime="low", description=ok)
    KeyLevel(type="support", price="1", description=ok)
    with pytest.raises(ValidationError):
        TrendContext(direction="up", strength="weak", description=too_long)
    with pytest.raises(ValidationError):
        VolatilityContext(regime="low", description=too_long)
    with pytest.raises(ValidationError):
        KeyLevel(type="support", price="1", description=too_long)


@pytest.mark.parametrize("level_type", ["support", "resistance"])
def test_key_level_types(level_type):
    assert KeyLevel(type=level_type, price="3639.50", description="d").type.value == level_type


@pytest.mark.parametrize("changes", [{"price": "0"}, {"price": "-1"}, {"price": 3639.5}, {"type": "pivot"}, {"target": "1"}])
def test_invalid_key_level(changes):
    with pytest.raises(ValidationError):
        KeyLevel.model_validate({"type": "support", "price": "3639.50", "description": "d", **changes})


def test_model_metadata(make):
    data = make.analysis()["model_metadata"]
    ModelMetadata.model_validate(data)
    for bad in [{"generated_at_utc": "2026-09-18T14:30:04"}, {"reasoning": "hidden"}, {"chain_of_thought": "..."}]:
        with pytest.raises(ValidationError):
            ModelMetadata.model_validate({**data, **bad})
    for field in data:
        partial = {k: v for k, v in data.items() if k != field}
        with pytest.raises(ValidationError):
            ModelMetadata.model_validate(partial)


def test_valid_analysis_and_round_trip(make):
    analysis = MarketAnalysis.model_validate(make.analysis())
    assert MarketAnalysis.model_validate_json(analysis.model_dump_json()) == analysis
    assert analysis.model_dump(mode="json") == make.analysis()


def test_analysis_allows_empty_lists(make):
    data = {**make.analysis(), "key_levels": [], "market_observations": [], "uncertainties": []}
    MarketAnalysis.model_validate(data)


@pytest.mark.parametrize("version", ["1.0.0", "1.1.0", "2.0.0", "0.9.3"])
def test_schema_version_is_any_valid_semver(make, version):
    assert MarketAnalysis.model_validate({**make.analysis(), "schema_version": version}).schema_version == version


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0-rc1", "", "latest"])
def test_invalid_schema_version(make, version):
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**make.analysis(), "schema_version": version})


@pytest.mark.parametrize("field", ["market_observations", "uncertainties"])
def test_text_list_limits(make, field):
    base = make.analysis()
    MarketAnalysis.model_validate({**base, field: ["x" * 500] * 20})
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**base, field: ["x"] * 21})
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**base, field: ["x" * 501]})


def test_key_levels_limit(make):
    level = {"type": "support", "price": "1", "description": "d"}
    base = make.analysis()
    MarketAnalysis.model_validate({**base, "key_levels": [level] * 20})
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**base, "key_levels": [level] * 21})


@pytest.mark.parametrize("version_changes", [{"analysis_id": "7c2e1ef6-1c88-1a3a-87f5-f3d5c9a0f11e"}, {"analysis_id": "nope"}])
def test_analysis_id_must_be_uuid4(make, version_changes):
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**make.analysis(), **version_changes})


def test_timestamp_must_be_utc(make):
    for bad in ["2026-09-18T14:30:05", "2026-09-18T16:30:05+02:00"]:
        with pytest.raises(ValidationError):
            MarketAnalysis.model_validate({**make.analysis(), "timestamp_utc": bad})


@pytest.mark.parametrize(
    "field",
    [
        "schema_version", "analysis_id", "timestamp_utc", "symbol", "timeframe", "market_snapshot",
        "trend_context", "volatility_context", "key_levels", "market_observations", "uncertainties",
        "data_sources", "model_metadata",
    ],
)
def test_every_field_is_required(make, field):
    data = make.analysis()
    del data[field]
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)


@pytest.mark.parametrize(
    "forbidden",
    ["buy", "sell", "entry_price", "stop_loss", "take_profit", "position_size", "broker_order_id", "status", "reasoning"],
)
def test_trading_and_lifecycle_fields_are_rejected(make, forbidden):
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**make.analysis(), forbidden: "x"})


def test_data_sources_must_include_snapshot_source(make):
    data = make.analysis()
    data["data_sources"] = []
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)
    data["data_sources"] = [{**make.source(), "provider_name": "Other"}]
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)


def test_data_sources_may_hold_additional_sources(make):
    data = make.analysis()
    data["data_sources"] = [make.source(), {**make.source(), "provider_name": "Other"}]
    MarketAnalysis.model_validate(data)


def test_live_provenance_is_preserved_and_distinct(make):
    data = make.analysis()
    live = {**make.source(), "mode": "live"}
    data["market_snapshot"]["data_source"] = live
    data["data_sources"] = [live]
    parsed = MarketAnalysis.model_validate(data)
    assert parsed.data_sources[0].mode.value == "live"
    assert parsed.model_dump(mode="json")["market_snapshot"]["data_source"]["mode"] == "live"


def test_symbol_and_timeframe_must_match_snapshot(make):
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**make.analysis(), "timeframe": "4h"})
    data = make.analysis()
    data["market_snapshot"]["timeframe"] = "4h"
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate({**make.analysis(), "symbol": "EURUSD"})
