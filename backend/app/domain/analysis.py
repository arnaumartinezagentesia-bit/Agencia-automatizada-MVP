from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from app.domain.base import ContractModel
from app.domain.enums import (
    Instrument,
    KeyLevelType,
    Timeframe,
    TrendDirection,
    TrendStrength,
    VolatilityRegime,
)
from app.domain.market import DataSource, MarketSnapshot
from app.domain.types import NonEmptyStr, PositiveDecimalString, SemVer, UtcDatetime, Uuid4

Description = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=2000)]
ShortText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=500)]


class TrendContext(ContractModel):
    direction: TrendDirection
    strength: TrendStrength
    description: Description


class VolatilityContext(ContractModel):
    regime: VolatilityRegime
    description: Description


class KeyLevel(ContractModel):
    type: KeyLevelType
    price: PositiveDecimalString
    description: Description


class ModelMetadata(ContractModel):
    provider: NonEmptyStr
    model: NonEmptyStr
    prompt_version: NonEmptyStr
    generated_at_utc: UtcDatetime


class MarketAnalysis(ContractModel):
    schema_version: SemVer
    analysis_id: Uuid4
    timestamp_utc: UtcDatetime
    symbol: Instrument
    timeframe: Timeframe
    market_snapshot: MarketSnapshot
    trend_context: TrendContext
    volatility_context: VolatilityContext
    key_levels: Annotated[list[KeyLevel], Field(max_length=20)]
    market_observations: Annotated[list[ShortText], Field(max_length=20)]
    uncertainties: Annotated[list[ShortText], Field(max_length=20)]
    data_sources: list[DataSource]
    model_metadata: ModelMetadata

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.symbol != self.market_snapshot.symbol:
            raise ValueError("symbol must match market_snapshot.symbol")
        if self.timeframe != self.market_snapshot.timeframe:
            raise ValueError("timeframe must match market_snapshot.timeframe")
        if self.market_snapshot.data_source not in self.data_sources:
            raise ValueError("data_sources must include market_snapshot.data_source")
        return self
