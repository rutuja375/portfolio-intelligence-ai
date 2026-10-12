
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.market_data.alpaca_provider import fetch_regular_session_bars


def make_bar(minute: int, close: float = 100.0):
    """Create a valid synthetic market-data bar."""
    return SimpleNamespace(
        timestamp=datetime(2026, 10, 5, 13, minute, tzinfo=UTC),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=100,
    )


class FakeAlpacaClient:
    """Return predefined market data without making API requests."""

    def __init__(self, data):
        self.data = data
        self.requests = []

    def get_stock_bars(self, request):
        self.requests.append(request)
        return SimpleNamespace(data=self.data)


def test_fetch_multiple_symbols():
    client = FakeAlpacaClient(
        {
            "NVDA": [make_bar(30), make_bar(31)],
            "AAPL": [make_bar(30)],
            "MSFT": [make_bar(30)],
        }
    )

    start = datetime(2026, 10, 5, 13, 0, tzinfo=UTC)
    end = datetime(2026, 10, 5, 20, 0, tzinfo=UTC)

    result = fetch_regular_session_bars(
        client,
        ["NVDA", "AAPL", "MSFT"],
        start,
        end,
    )

    assert set(result) == {"NVDA", "AAPL", "MSFT"}
    assert len(result["NVDA"]) == 2
    assert len(result["AAPL"]) == 1
    assert len(result["MSFT"]) == 1
    assert len(client.requests) == 1

    request = client.requests[0]
    assert request.symbol_or_symbols == ["NVDA", "AAPL", "MSFT"]
    assert request.feed.value == "iex"


def test_fetch_filters_premarket_bars():
    client = FakeAlpacaClient(
        {
            "NVDA": [
                SimpleNamespace(
                    timestamp=datetime(2026, 10, 5, 12, 30, tzinfo=UTC),
                    open=100.0,
                    high=100.0,
                    low=100.0,
                    close=100.0,
                    volume=100,
                ),
                make_bar(30),
            ]
        }
    )

    result = fetch_regular_session_bars(
        client,
        ["NVDA"],
        datetime(2026, 10, 5, 12, 0, tzinfo=UTC),
        datetime(2026, 10, 5, 20, 0, tzinfo=UTC),
    )

    assert len(result["NVDA"]) == 1
    assert result["NVDA"][0].timestamp.hour == 13


def test_fetch_preserves_missing_symbol():
    client = FakeAlpacaClient({"NVDA": [make_bar(30)]})

    result = fetch_regular_session_bars(
        client,
        ["NVDA", "AAPL"],
        datetime(2026, 10, 5, 13, 0, tzinfo=UTC),
        datetime(2026, 10, 5, 20, 0, tzinfo=UTC),
    )

    assert len(result["NVDA"]) == 1
    assert result["AAPL"] == []


def test_fetch_rejects_empty_symbols():
    client = FakeAlpacaClient({})

    with pytest.raises(
        ValueError,
        match="At least one stock symbol is required",
    ):
        fetch_regular_session_bars(
            client,
            [],
            datetime(2026, 10, 5, 13, 0, tzinfo=UTC),
            datetime(2026, 10, 5, 20, 0, tzinfo=UTC),
        )

    assert client.requests == []
