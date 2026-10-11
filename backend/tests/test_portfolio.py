
import pytest
from app.analytics.portfolio import (
    calculate_contribution,
    calculate_portfolio_contributions,
    calculate_portfolio_return,
    validate_portfolio_weights,
)


@pytest.mark.parametrize(
    ("weight", "stock_return", "expected"),
    [
        (0.40, 0.02, 0.008),
        (0.35, -0.01, -0.0035),
        (0.25, 0.015, 0.00375),
        (0.50, 0.0, 0.0),
        (0.0, 0.05, 0.0),
        (1.0, 0.02, 0.02),
    ],
)
def test_calculate_contribution(weight, stock_return, expected):
    assert calculate_contribution(weight, stock_return) == pytest.approx(expected)


@pytest.mark.parametrize("weight", [-0.1, 1.1])
def test_invalid_weight(weight):
    with pytest.raises(
        ValueError,
        match="Portfolio weight must be between 0 and 1",
    ):
        calculate_contribution(weight, 0.02)

def test_valid_portfolio_weights():
    weights = {"NVDA": 0.40, "AAPL": 0.35, "MSFT": 0.25}
    validate_portfolio_weights(weights)


@pytest.mark.parametrize(
    "weights",
    [
        {},
        {"NVDA": 0.50, "AAPL": 0.25},
        {"NVDA": 0.60, "AAPL": 0.50},
        {"NVDA": -0.10, "AAPL": 1.10},
    ],
)
def test_invalid_portfolio_weights(weights):
    with pytest.raises(ValueError):
        validate_portfolio_weights(weights)


def test_portfolio_return():
    weights = {"NVDA": 0.40, "AAPL": 0.35, "MSFT": 0.25}
    returns = {"NVDA": 0.02, "AAPL": -0.01, "MSFT": 0.015}

    result = calculate_portfolio_return(weights, returns)

    assert result == pytest.approx(0.00825)


def test_portfolio_return_missing_holding():
    weights = {"NVDA": 0.60, "AAPL": 0.40}
    returns = {"NVDA": 0.02}

    with pytest.raises(
        ValueError,
        match="Portfolio holdings and stock returns must match",
    ):
        calculate_portfolio_return(weights, returns)


def test_portfolio_contributions():
    weights = {"NVDA": 0.40, "AAPL": 0.35, "MSFT": 0.25}
    returns = {"NVDA": 0.02, "AAPL": -0.01, "MSFT": 0.015}

    contributions = calculate_portfolio_contributions(weights, returns)

    assert contributions == pytest.approx(
        {
            "NVDA": 0.008,
            "AAPL": -0.0035,
            "MSFT": 0.00375,
        }
    )


def test_contributions_sum_to_portfolio_return():
    weights = {"NVDA": 0.40, "AAPL": 0.35, "MSFT": 0.25}
    returns = {"NVDA": 0.02, "AAPL": -0.01, "MSFT": 0.015}

    contributions = calculate_portfolio_contributions(weights, returns)
    portfolio_return = calculate_portfolio_return(weights, returns)

    assert sum(contributions.values()) == pytest.approx(portfolio_return)


def test_contributions_reject_missing_returns():
    weights = {"NVDA": 0.60, "AAPL": 0.40}
    returns = {"NVDA": 0.02}

    with pytest.raises(
        ValueError,
        match="Portfolio holdings and stock returns must match",
    ):
        calculate_portfolio_contributions(weights, returns)
