from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.market_data.quality import assess_data_quality


def test_quality_report_exposes_missing_and_stale_data():
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = {
        "AAPL": [
            SimpleNamespace(timestamp=start, close=100.0, volume=10),
            SimpleNamespace(timestamp=start + timedelta(minutes=1), close=100.0, volume=0),
        ],
        "MSFT": [SimpleNamespace(timestamp=start, close=200.0, volume=10)],
    }
    aligned = {
        start: {"AAPL": 100.0, "MSFT": 200.0},
        start + timedelta(minutes=1): {"AAPL": 100.0, "MSFT": None},
    }
    report = assess_data_quality(bars, aligned)
    assert report.coverage == 0.5
    assert report.missing_prices["MSFT"] == 1
    assert report.stale_intervals["AAPL"] == 1
    assert len(report.warnings) == 2
