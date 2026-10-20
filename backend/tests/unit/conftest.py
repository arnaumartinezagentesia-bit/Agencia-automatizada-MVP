"""Builders for JSON-shaped contract payloads (fresh copy per call, safe to mutate)."""

import pytest

ANALYSIS_ID = "7c2e1ef6-1c88-4a3a-87f5-f3d5c9a0f11e"
REQUEST_ID = "c9c52d62-5e0b-4a11-bc61-89e7a9f4e9b4"
EVENT_ID = "8f0a7f29-0f8e-4b0f-93c7-f4c6e2bf56c2"
COMPLETED_AT = "2026-09-18T14:30:05Z"


def _request():
    return {"symbol": "XAUUSD", "timeframe": "1h", "data_mode": "fixture"}


def _bar(hour=13):
    return {
        "timestamp_utc": f"2026-09-18T{hour:02d}:00:00Z",
        "open": "3640.10",
        "high": "3643.00",
        "low": "3639.50",
        "close": "3642.15",
        "volume": "1234.56",
    }


def _source():
    return {
        "mode": "fixture",
        "provider_name": "FixtureMarketDataProvider",
        "provider_version": "1.0.0",
        "retrieved_at_utc": "2026-09-18T14:30:01Z",
        "source_as_of_utc": "2026-09-18T14:30:00Z",
    }


def _snapshot():
    return {
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "as_of_utc": "2026-09-18T14:30:00Z",
        "bid": "3642.15",
        "ask": "3642.25",
        "mid": "3642.20",
        "bars": [_bar(12), _bar(13), _bar(14)],
        "data_source": _source(),
    }


def _analysis():
    return {
        "schema_version": "1.0.0",
        "analysis_id": ANALYSIS_ID,
        "timestamp_utc": COMPLETED_AT,
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "market_snapshot": _snapshot(),
        "trend_context": {"direction": "up", "strength": "moderate", "description": "Higher closes."},
        "volatility_context": {"regime": "moderate", "description": "Ranges are stable."},
        "key_levels": [{"type": "support", "price": "3639.50", "description": "Recent low."}],
        "market_observations": ["Price is above the recent range midpoint."],
        "uncertainties": ["Sample does not include a major event window."],
        "data_sources": [_source()],
        "model_metadata": {
            "provider": "fake",
            "model": "fake-model",
            "prompt_version": "market-intelligence-v1",
            "generated_at_utc": "2026-09-18T14:30:04Z",
        },
    }


def _run(status="pending"):
    run = {
        "analysis_id": ANALYSIS_ID,
        "status": status,
        "created_at_utc": "2026-09-18T14:30:00Z",
        "started_at_utc": None,
        "completed_at_utc": None,
        "failed_at_utc": None,
        "request_id": REQUEST_ID,
        "request": _request(),
        "error": None,
        "analysis": None,
    }
    if status in ("running", "completed", "failed"):
        run["started_at_utc"] = "2026-09-18T14:30:00Z"
    if status == "completed":
        run["completed_at_utc"] = COMPLETED_AT
        run["analysis"] = _analysis()
    if status == "failed":
        run["failed_at_utc"] = COMPLETED_AT
        run["error"] = {"code": "PROVIDER_ERROR", "message": "Market data provider failed."}
    return run


@pytest.fixture
def make():
    class Make:
        request = staticmethod(_request)
        bar = staticmethod(_bar)
        source = staticmethod(_source)
        snapshot = staticmethod(_snapshot)
        analysis = staticmethod(_analysis)
        run = staticmethod(_run)

    return Make
