import pytest
from pydantic import ValidationError

from app.domain.market import DataSource, MarketBar, MarketSnapshot


def test_valid_bar_and_zero_volume(make):
    MarketBar.model_validate(make.bar())
    MarketBar.model_validate({**make.bar(), "volume": "0"})


def test_flat_bar_is_valid(make):
    flat = {**make.bar(), "open": "10", "high": "10", "low": "10", "close": "10"}
    MarketBar.model_validate(flat)


@pytest.mark.parametrize(
    "changes",
    [
        {"high": "3642.00"},  # high < close
        {"high": "3640.00"},  # high < open
        {"low": "3640.20"},  # low > open
        {"low": "3643.50"},  # low > close and > high
        {"high": "3639.00", "low": "3639.50"},  # high < low
        {"open": "0"},
        {"high": "0"},
        {"low": "0"},
        {"close": "0"},
        {"volume": "-1"},
        {"open": 3640.1},
        {"volume": 5},
        {"timestamp_utc": "2026-09-18T13:00:00"},
        {"timestamp_utc": "2026-09-18T15:00:00+02:00"},
    ],
)
def test_invalid_bar(make, changes):
    with pytest.raises(ValidationError):
        MarketBar.model_validate({**make.bar(), **changes})


@pytest.mark.parametrize("field", ["timestamp_utc", "open", "high", "low", "close", "volume"])
def test_bar_requires_every_field(make, field):
    data = make.bar()
    del data[field]
    with pytest.raises(ValidationError):
        MarketBar.model_validate(data)


def test_bar_has_no_symbol_or_timeframe_field(make):
    assert set(MarketBar.model_fields) == {"timestamp_utc", "open", "high", "low", "close", "volume"}
    with pytest.raises(ValidationError):
        MarketBar.model_validate({**make.bar(), "symbol": "XAUUSD"})


def test_data_source_valid_for_both_modes(make):
    for mode in ("fixture", "live"):
        assert DataSource.model_validate({**make.source(), "mode": mode}).mode.value == mode


@pytest.mark.parametrize(
    "changes",
    [
        {"mode": "demo"},
        {"mode": "FIXTURE"},
        {"retrieved_at_utc": "2026-09-18T14:30:01"},
        {"source_as_of_utc": "2026-09-18T16:30:00+02:00"},
        {"provider_name": 5},
        {"extra_field": 1},
    ],
)
def test_invalid_data_source(make, changes):
    with pytest.raises(ValidationError):
        DataSource.model_validate({**make.source(), **changes})


@pytest.mark.parametrize("field", ["mode", "provider_name", "provider_version", "retrieved_at_utc", "source_as_of_utc"])
def test_data_source_requires_every_field(make, field):
    data = make.source()
    del data[field]
    with pytest.raises(ValidationError):
        DataSource.model_validate(data)


def test_valid_snapshot(make):
    snap = MarketSnapshot.model_validate(make.snapshot())
    assert len(snap.bars) == 3


def test_snapshot_allows_empty_bars(make):
    assert MarketSnapshot.model_validate({**make.snapshot(), "bars": []}).bars == []


def test_snapshot_allows_ask_equal_bid_and_last_bar_equal_as_of(make):
    data = {**make.snapshot(), "bid": "10", "ask": "10", "mid": "10"}
    data["as_of_utc"] = data["bars"][-1]["timestamp_utc"]
    MarketSnapshot.model_validate(data)


def test_mid_is_not_required_to_equal_the_average(make):
    # Gate decision: no exact-equality or tolerance rule for mid.
    MarketSnapshot.model_validate({**make.snapshot(), "mid": "9999"})


@pytest.mark.parametrize(
    "changes",
    [
        {"bid": "0"},
        {"ask": "0"},
        {"mid": "0"},
        {"ask": "3642.00"},  # ask < bid
        {"bid": 3642.15},
        {"symbol": "EURUSD"},
        {"symbol": "XAU/USD"},
        {"timeframe": "2h"},
        {"as_of_utc": "2026-09-18T14:30:00"},
        {"data_source": None},
        {"extra_field": 1},
    ],
)
def test_invalid_snapshot_fields(make, changes):
    with pytest.raises(ValidationError):
        MarketSnapshot.model_validate({**make.snapshot(), **changes})


def test_snapshot_rejects_duplicate_bar_timestamps(make):
    data = make.snapshot()
    data["bars"] = [make.bar(12), make.bar(13), make.bar(13)]
    with pytest.raises(ValidationError):
        MarketSnapshot.model_validate(data)


def test_snapshot_rejects_unordered_bars(make):
    data = make.snapshot()
    data["bars"] = [make.bar(13), make.bar(12)]
    with pytest.raises(ValidationError):
        MarketSnapshot.model_validate(data)


def test_snapshot_rejects_last_bar_after_as_of(make):
    data = make.snapshot()
    data["bars"] = [make.bar(13), make.bar(15)]
    with pytest.raises(ValidationError):
        MarketSnapshot.model_validate(data)


def test_snapshot_rejects_invalid_nested_bar(make):
    data = make.snapshot()
    data["bars"][0]["high"] = "1"
    with pytest.raises(ValidationError):
        MarketSnapshot.model_validate(data)


def test_snapshot_json_round_trip(make):
    snap = MarketSnapshot.model_validate(make.snapshot())
    again = MarketSnapshot.model_validate_json(snap.model_dump_json())
    assert again == snap
    dumped = snap.model_dump(mode="json")
    assert dumped == make.snapshot()
    assert dumped["bid"] == "3642.15"
