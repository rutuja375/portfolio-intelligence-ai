
from datetime import UTC, datetime
from types import SimpleNamespace

from app.market_data.alignment import align_bars_by_timestamp


def make_bar(minute: int, close: float):
    return SimpleNamespace(
        timestamp=datetime(2026, 10, 5, 13, minute, tzinfo=UTC),
        close=close,
    )


def test_aligns_bars_and_preserves_missing_prices():
    bars_by_symbol = {
        "NVDA": [
            make_bar(30, 200.0),
            make_bar(31, 201.0),
            make_bar(32, 202.0),
        ],
        "AAPL": [
            make_bar(30, 250.0),
            make_bar(32, 251.0),
        ],
        "MSFT": [
            make_bar(30, 400.0),
            make_bar(31, 401.0),
            make_bar(32, 402.0),
        ],
    }

    aligned = align_bars_by_timestamp(bars_by_symbol)

    t_1030 = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)
    t_1031 = datetime(2026, 10, 5, 13, 31, tzinfo=UTC)
    t_1032 = datetime(2026, 10, 5, 13, 32, tzinfo=UTC)

    assert aligned[t_1030] == {
        "NVDA": 200.0,
        "AAPL": 250.0,
        "MSFT": 400.0,
    }
    assert aligned[t_1031] == {
        "NVDA": 201.0,
        "AAPL": None,
        "MSFT": 401.0,
    }
    assert aligned[t_1032] == {
        "NVDA": 202.0,
        "AAPL": 251.0,
        "MSFT": 402.0,
    }


def test_aligns_unsorted_input():
    bars_by_symbol = {
        "NVDA": [
            make_bar(32, 202.0),
            make_bar(30, 200.0),
        ],
    }

    aligned = align_bars_by_timestamp(bars_by_symbol)

    assert list(aligned) == [
        datetime(2026, 10, 5, 13, 30, tzinfo=UTC),
        datetime(2026, 10, 5, 13, 32, tzinfo=UTC),
    ]


def test_preserves_symbol_with_no_bars():
    bars_by_symbol = {
        "NVDA": [make_bar(30, 200.0)],
        "AAPL": [],
    }

    aligned = align_bars_by_timestamp(bars_by_symbol)

    timestamp = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    assert aligned[timestamp] == {
        "NVDA": 200.0,
        "AAPL": None,
    }


def test_empty_input():
    assert align_bars_by_timestamp({}) == {}
