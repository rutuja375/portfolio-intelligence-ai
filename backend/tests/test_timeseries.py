
from datetime import UTC, datetime, timedelta

import pytest
from app.analytics.timeseries import calculate_synchronized_portfolio_returns


def test_synchronized_portfolio_return():
    start = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    aligned_prices = {
        start: {
            "NVDA": 200.0,
            "AAPL": 250.0,
            "MSFT": 400.0,
        },
        start + timedelta(minutes=1): {
            "NVDA": 202.0,
            "AAPL": 249.0,
            "MSFT": 404.0,
        },
    }

    weights = {
        "NVDA": 0.40,
        "AAPL": 0.35,
        "MSFT": 0.25,
    }

    results = calculate_synchronized_portfolio_returns(
        aligned_prices,
        weights,
    )

    assert len(results) == 1

    result = results[0]

    assert result["timestamp"] == start + timedelta(minutes=1)

    assert result["stock_returns"]["NVDA"] == pytest.approx(0.01)
    assert result["stock_returns"]["AAPL"] == pytest.approx(-0.004)
    assert result["stock_returns"]["MSFT"] == pytest.approx(0.01)

    assert result["contributions"]["NVDA"] == pytest.approx(0.004)
    assert result["contributions"]["AAPL"] == pytest.approx(-0.0014)
    assert result["contributions"]["MSFT"] == pytest.approx(0.0025)

    assert result["portfolio_return"] == pytest.approx(0.0051)


def test_skips_missing_stock_price():
    start = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    aligned_prices = {
        start: {
            "NVDA": 200.0,
            "AAPL": 250.0,
            "MSFT": 400.0,
        },
        start + timedelta(minutes=1): {
            "NVDA": 201.0,
            "AAPL": None,
            "MSFT": 401.0,
        },
        start + timedelta(minutes=2): {
            "NVDA": 202.0,
            "AAPL": 251.0,
            "MSFT": 402.0,
        },
        start + timedelta(minutes=3): {
            "NVDA": 203.0,
            "AAPL": 252.0,
            "MSFT": 403.0,
        },
    }

    weights = {
        "NVDA": 0.40,
        "AAPL": 0.35,
        "MSFT": 0.25,
    }

    results = calculate_synchronized_portfolio_returns(
        aligned_prices,
        weights,
    )

    assert len(results) == 1
    assert results[0]["timestamp"] == start + timedelta(minutes=3)


def test_skips_nonconsecutive_timestamps():
    start = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    aligned_prices = {
        start: {"NVDA": 200.0},
        start + timedelta(minutes=2): {"NVDA": 202.0},
    }

    results = calculate_synchronized_portfolio_returns(
        aligned_prices,
        {"NVDA": 1.0},
    )

    assert results == []


def test_rejects_invalid_portfolio_weights():
    start = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    aligned_prices = {
        start: {"NVDA": 200.0},
        start + timedelta(minutes=1): {"NVDA": 201.0},
    }

    with pytest.raises(ValueError, match="sum to 1.0"):
        calculate_synchronized_portfolio_returns(
            aligned_prices,
            {"NVDA": 0.5},
        )


def test_synchronized_contributions_sum_to_portfolio_return():
    start = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)

    aligned_prices = {
        start: {
            "NVDA": 200.0,
            "AAPL": 250.0,
            "MSFT": 400.0,
        },
        start + timedelta(minutes=1): {
            "NVDA": 202.0,
            "AAPL": 249.0,
            "MSFT": 404.0,
        },
    }

    weights = {
        "NVDA": 0.40,
        "AAPL": 0.35,
        "MSFT": 0.25,
    }

    results = calculate_synchronized_portfolio_returns(
        aligned_prices,
        weights,
    )

    assert len(results) == 1

    result = results[0]

    assert sum(result["contributions"].values()) == pytest.approx(
        result["portfolio_return"]
    )
