
from datetime import datetime, timedelta
from itertools import pairwise

from app.analytics.portfolio import (
    calculate_portfolio_contributions,
    calculate_portfolio_return,
    validate_portfolio_weights,
)
from app.analytics.returns import calculate_simple_return


def calculate_synchronized_portfolio_returns(
    aligned_prices: dict[datetime, dict[str, float | None]],
    weights: dict[str, float],
) -> list[dict]:
    """Calculate portfolio returns for fully observed consecutive minutes."""

    validate_portfolio_weights(weights)

    results = []

    for (previous_time, previous_prices), (
        current_time,
        current_prices,
    ) in pairwise(sorted(aligned_prices.items())):

        # Only calculate returns for consecutive one-minute observations.
        if current_time - previous_time != timedelta(minutes=1):
            continue

        # Every portfolio holding must have prices at both timestamps.
        if (
            previous_prices.keys() != weights.keys()
            or current_prices.keys() != weights.keys()
        ):
            continue

        if any(
            previous_prices[symbol] is None
            or current_prices[symbol] is None
            for symbol in weights
        ):
            continue

        stock_returns = {
            symbol: calculate_simple_return(
                previous_prices[symbol],
                current_prices[symbol],
            )
            for symbol in weights
        }

        contributions = calculate_portfolio_contributions(
            weights,
            stock_returns,
        )

        portfolio_return = calculate_portfolio_return(
            weights,
            stock_returns,
        )

        results.append(
            {
                "timestamp": current_time,
                "stock_returns": stock_returns,
                "contributions": contributions,
                "portfolio_return": portfolio_return,
            }
        )

    return results

