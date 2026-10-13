from dataclasses import dataclass
from datetime import datetime
from statistics import median


@dataclass(frozen=True)
class Anomaly:
    timestamp: datetime
    value: float
    score: float
    direction: str
    method: str = "rolling_mad"


def detect_rolling_anomalies(
    observations: list[tuple[datetime, float]],
    *,
    window: int = 30,
    threshold: float = 3.5,
) -> list[Anomaly]:
    """Detect point anomalies with a trailing, leakage-free robust z-score."""
    if window < 3:
        raise ValueError("Window must contain at least three observations")
    anomalies = []
    for index in range(window, len(observations)):
        timestamp, value = observations[index]
        history = [item[1] for item in observations[index - window:index]]
        center = median(history)
        mad = median(abs(item - center) for item in history)
        if mad == 0:
            continue
        score = 0.6744897501960817 * (value - center) / mad
        if abs(score) >= threshold:
            anomalies.append(
                Anomaly(
                    timestamp=timestamp,
                    value=value,
                    score=score,
                    direction="up" if score > 0 else "down",
                )
            )
    return anomalies


@dataclass(frozen=True)
class MarketContext:
    asset_return: float
    market_return: float
    sector_return: float | None
    beta: float | None
    market_adjusted_return: float
    sector_adjusted_return: float | None


def estimate_beta(asset_history: list[float], market_history: list[float]) -> float | None:
    if len(asset_history) != len(market_history) or len(asset_history) < 3:
        return None
    market_mean = sum(market_history) / len(market_history)
    asset_mean = sum(asset_history) / len(asset_history)
    variance = sum((value - market_mean) ** 2 for value in market_history)
    if variance == 0:
        return None
    covariance = sum(
        (market - market_mean) * (asset - asset_mean)
        for asset, market in zip(asset_history, market_history, strict=True)
    )
    return covariance / variance


def contextualize_return(
    asset_return: float,
    market_return: float,
    *,
    sector_return: float | None = None,
    asset_history: list[float] | None = None,
    market_history: list[float] | None = None,
) -> MarketContext:
    beta = estimate_beta(asset_history or [], market_history or [])
    expected = market_return if beta is None else beta * market_return
    return MarketContext(
        asset_return=asset_return,
        market_return=market_return,
        sector_return=sector_return,
        beta=beta,
        market_adjusted_return=asset_return - expected,
        sector_adjusted_return=(
            None if sector_return is None else asset_return - sector_return
        ),
    )
