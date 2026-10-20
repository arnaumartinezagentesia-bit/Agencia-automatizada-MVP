"""Mandatory text fields reject "" (Phase 2 gate); empty lists stay valid; content is never altered."""

import pytest
from pydantic import ValidationError

from app.domain.analysis import KeyLevel, MarketAnalysis, ModelMetadata, TrendContext, VolatilityContext
from app.domain.errors import ErrorDetail
from app.domain.events import ErrorSummary
from app.domain.market import DataSource


def _set(data, path, value):
    *parents, last = path.split(".")
    for key in parents:
        data = data[int(key)] if key.isdigit() else data[key]
    if last.isdigit():
        data[int(last)] = value
    else:
        data[last] = value


@pytest.mark.parametrize(
    "path",
    [
        "trend_context.description",
        "volatility_context.description",
        "key_levels.0.description",
        "market_observations.0",
        "uncertainties.0",
        "model_metadata.provider",
        "model_metadata.model",
        "model_metadata.prompt_version",
        "market_snapshot.data_source.provider_name",
        "market_snapshot.data_source.provider_version",
        "data_sources.0.provider_name",
        "data_sources.0.provider_version",
    ],
)
def test_analysis_rejects_empty_string_in_text_field(make, path):
    data = make.analysis()
    _set(data, path, "")
    with pytest.raises(ValidationError):
        MarketAnalysis.model_validate(data)


@pytest.mark.parametrize("field", ["provider_name", "provider_version"])
def test_data_source_rejects_empty_string(make, field):
    with pytest.raises(ValidationError):
        DataSource.model_validate({**make.source(), field: ""})


@pytest.mark.parametrize("field", ["provider", "model", "prompt_version"])
def test_model_metadata_rejects_empty_string(make, field):
    with pytest.raises(ValidationError):
        ModelMetadata.model_validate({**make.analysis()["model_metadata"], field: ""})


def test_contexts_and_key_level_reject_empty_description():
    with pytest.raises(ValidationError):
        TrendContext(direction="up", strength="weak", description="")
    with pytest.raises(ValidationError):
        VolatilityContext(regime="low", description="")
    with pytest.raises(ValidationError):
        KeyLevel(type="support", price="1", description="")


def test_error_messages_reject_empty_string():
    with pytest.raises(ValidationError):
        ErrorDetail(code="LLM_ERROR", message="")
    with pytest.raises(ValidationError):
        ErrorSummary(code="LLM_ERROR", message="")


def test_error_details_stay_arbitrary_json_object():
    assert ErrorDetail(code="LLM_ERROR", message="m", details={"": "", "k": ""}).details == {"": "", "k": ""}
    assert ErrorDetail(code="LLM_ERROR", message="m", details={}).details == {}


def test_empty_lists_remain_valid(make):
    data = {**make.analysis(), "key_levels": [], "market_observations": [], "uncertainties": []}
    data["market_snapshot"]["bars"] = []
    MarketAnalysis.model_validate(data)


def test_text_is_not_trimmed_or_normalized(make):
    data = make.analysis()
    data["market_observations"] = ["  Mixed Case  "]
    parsed = MarketAnalysis.model_validate(data)
    assert parsed.market_observations == ["  Mixed Case  "]
    assert parsed.model_dump(mode="json")["market_observations"] == ["  Mixed Case  "]
