from decimal import Decimal
from typing import Self

from pydantic import model_validator

from app.domain.base import ContractModel
from app.domain.enums import DataSourceMode, Instrument, Timeframe
from app.domain.types import (
    NonEmptyStr,
    NonNegativeDecimalString,
    PositiveDecimalString,
    UtcDatetime,
)


class MarketBar(ContractModel):
    timestamp_utc: UtcDatetime
    open: PositiveDecimalString
    high: PositiveDecimalString
    low: PositiveDecimalString
    close: PositiveDecimalString
    volume: NonNegativeDecimalString

    @model_validator(mode="after")
    def _check_ohlc(self) -> Self:
        o, h, l, c = (Decimal(x) for x in (self.open, self.high, self.low, self.close))
        if h < max(o, c):
            raise ValueError("high must be >= max(open, close)")
        if l > min(o, c):
            raise ValueError("low must be <= min(open, close)")
        if h < l:
            raise ValueError("high must be >= low")
        return self


class DataSource(ContractModel):
    mode: DataSourceMode
    provider_name: NonEmptyStr
    provider_version: NonEmptyStr
    retrieved_at_utc: UtcDatetime
    source_as_of_utc: UtcDatetime


class MarketSnapshot(ContractModel):
    symbol: Instrument
    timeframe: Timeframe
    as_of_utc: UtcDatetime
    bid: PositiveDecimalString
    ask: PositiveDecimalString
    mid: PositiveDecimalString
    bars: list[MarketBar]
    data_source: DataSource

    @model_validator(mode="after")
    def _check_snapshot(self) -> Self:
        if Decimal(self.ask) < Decimal(self.bid):
            raise ValueError("ask must be >= bid")
        stamps = [b.timestamp_utc for b in self.bars]
        if any(a >= b for a, b in zip(stamps, stamps[1:])):
            raise ValueError("bar timestamps must be strictly increasing")
        if stamps and stamps[-1] > self.as_of_utc:
            raise ValueError("latest bar must not be later than as_of_utc")
        return self
