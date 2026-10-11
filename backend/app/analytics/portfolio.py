
def calculate_contribution(weight: float, stock_return: float) -> float:
    """Calculate one holding's contribution to portfolio return."""
    if not 0 <= weight <= 1:
        raise ValueError("Portfolio weight must be between 0 and 1")

    return weight * stock_return


def validate_portfolio_weights(weights: dict[str, float]) -> None:
    """Ensure portfolio weights are valid and total 100%."""
    if not weights:
        raise ValueError("Portfolio cannot be empty")

    for symbol, weight in weights.items():
        if not 0 <= weight <= 1:
            raise ValueError(f"Invalid weight for {symbol}")

    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("Portfolio weights must sum to 1.0")


def calculate_portfolio_return(
    weights: dict[str, float],
    stock_returns: dict[str, float],
) -> float:
    """Calculate portfolio return from beginning-of-period weights."""
    validate_portfolio_weights(weights)

    if weights.keys() != stock_returns.keys():
        raise ValueError("Portfolio holdings and stock returns must match")

    total_return = 0.0

    for symbol, weight in weights.items():
        contribution = calculate_contribution(
            weight,
            stock_returns[symbol],
        )
        total_return += contribution

    return total_return


def calculate_portfolio_contributions(
    weights: dict[str, float],
    stock_returns: dict[str, float],
) -> dict[str, float]:
    """Calculate each holding's contribution to portfolio return."""
    validate_portfolio_weights(weights)

    if weights.keys() != stock_returns.keys():
        raise ValueError("Portfolio holdings and stock returns must match")

    return {
        symbol: calculate_contribution(weight, stock_returns[symbol])
        for symbol, weight in weights.items()
    }
