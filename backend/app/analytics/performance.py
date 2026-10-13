from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from math import prod


@dataclass(frozen=True)
class PerformancePoint:
    timestamp: datetime
    period_return: float
    cumulative_return: float
    wealth_index: float


def cumulative_performance(observations: Iterable[dict]) -> list[PerformancePoint]:
    """Compound synchronized portfolio returns without filling missing periods."""
    wealth = 1.0
    points: list[PerformancePoint] = []
    for observation in sorted(observations, key=lambda item: item["timestamp"]):
        period_return = float(observation["portfolio_return"])
        if period_return <= -1:
            raise ValueError("A period return cannot be less than or equal to -100%")
        wealth *= 1 + period_return
        points.append(
            PerformancePoint(
                timestamp=observation["timestamp"],
                period_return=period_return,
                cumulative_return=wealth - 1,
                wealth_index=wealth,
            )
        )
    return points


def compound_returns(returns: Iterable[float]) -> float:
    values = list(returns)
    if any(value <= -1 for value in values):
        raise ValueError("A period return cannot be less than or equal to -100%")
    return prod(1 + value for value in values) - 1
