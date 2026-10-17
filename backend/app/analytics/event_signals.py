from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from statistics import median, pstdev

from app.analytics.portfolio import (
    calculate_portfolio_contributions,
    calculate_portfolio_return,
)
from app.analytics.returns import calculate_simple_return


@dataclass(frozen=True)
class EventSignal:
    timestamp: datetime
    horizon_minutes: int
    portfolio_return: float
    mad_score: float
    volatility_score: float
    volume_ratio: float | None
    stock_returns: dict[str, float]
    contributions: dict[str, float]
    confirmed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _robust_score(value: float, history: list[float]) -> float | None:
    center = median(history)
    mad = median(abs(item - center) for item in history)
    if mad == 0:
        return None
    return 0.6744897501960817 * (value - center) / mad


def _volume_ratio(
    *,
    timestamps: list[datetime],
    end_index: int,
    horizon: int,
    bars: dict[str, dict[datetime, object]],
    weights: dict[str, float],
    baseline_windows: int,
) -> float | None:
    ratios = []
    for symbol, weight in weights.items():
        current_times = timestamps[end_index - horizon + 1 : end_index + 1]
        current = sum(float(bars[symbol][time].volume) for time in current_times)
        historical = []
        for offset in range(1, baseline_windows + 1):
            window_end = end_index - horizon * offset
            window_start = window_end - horizon + 1
            if window_start < 0:
                break
            historical.append(
                sum(
                    float(bars[symbol][time].volume)
                    for time in timestamps[window_start : window_end + 1]
                )
            )
        normal = median(historical) if historical else 0
        if normal > 0:
            ratios.append(weight * current / normal)
    return sum(ratios) if ratios else None


def calculate_multi_window_signals(
    bars_by_symbol: dict[str, list],
    weights: dict[str, float],
    *,
    horizons: tuple[int, ...] = (1, 5, 15),
    baseline_window: int = 30,
    threshold: float = 3.5,
    volatility_threshold: float = 2.0,
    volume_threshold: float = 1.5,
    confirmation_horizon: int = 5,
) -> list[EventSignal]:
    """Calculate leakage-free, multi-horizon portfolio event signals.

    A signal is confirmed only on the configured primary horizon and only when
    robust return, volatility and volume checks agree.
    """
    if baseline_window < 3:
        raise ValueError("Baseline window must contain at least three observations")
    if confirmation_horizon not in horizons:
        raise ValueError("Confirmation horizon must be included in horizons")

    bars = {
        symbol: {bar.timestamp: bar for bar in symbol_bars}
        for symbol, symbol_bars in bars_by_symbol.items()
    }
    timestamps = sorted(set.intersection(*(set(items) for items in bars.values())))
    signals = []
    for horizon in horizons:
        observations: list[tuple[int, float, dict[str, float], dict[str, float]]] = []
        for end_index in range(horizon, len(timestamps)):
            start_time = timestamps[end_index - horizon]
            end_time = timestamps[end_index]
            if end_time - start_time != timedelta(minutes=horizon):
                continue
            stock_returns = {
                symbol: calculate_simple_return(
                    bars[symbol][start_time].close,
                    bars[symbol][end_time].close,
                )
                for symbol in weights
            }
            contributions = calculate_portfolio_contributions(weights, stock_returns)
            observations.append(
                (
                    end_index,
                    calculate_portfolio_return(weights, stock_returns),
                    stock_returns,
                    contributions,
                )
            )

        for index in range(baseline_window, len(observations)):
            end_index, value, stock_returns, contributions = observations[index]
            history = [item[1] for item in observations[index - baseline_window : index]]
            mad_score = _robust_score(value, history)
            deviation = pstdev(history)
            volatility_score = (
                0.0 if deviation == 0 else (value - median(history)) / deviation
            )
            volume_ratio = _volume_ratio(
                timestamps=timestamps,
                end_index=end_index,
                horizon=horizon,
                bars=bars,
                weights=weights,
                baseline_windows=min(baseline_window, end_index // horizon),
            )
            robust_pass = mad_score is not None and abs(mad_score) >= threshold
            confirmed = (
                horizon == confirmation_horizon
                and robust_pass
                and abs(volatility_score) >= volatility_threshold
                and volume_ratio is not None
                and volume_ratio >= volume_threshold
            )
            if robust_pass:
                signals.append(
                    EventSignal(
                        timestamp=timestamps[end_index],
                        horizon_minutes=horizon,
                        portfolio_return=value,
                        mad_score=mad_score,
                        volatility_score=volatility_score,
                        volume_ratio=volume_ratio,
                        stock_returns=stock_returns,
                        contributions=contributions,
                        confirmed=confirmed,
                    )
                )
    return sorted(signals, key=lambda signal: (signal.timestamp, signal.horizon_minutes))


def group_confirmed_events(
    signals: list[EventSignal], *, gap_minutes: int = 5
) -> list[dict]:
    """Merge nearby confirmations into one event and retain its strongest signal."""
    confirmed = [signal for signal in signals if signal.confirmed]
    groups: list[list[EventSignal]] = []
    for signal in confirmed:
        if not groups or signal.timestamp - groups[-1][-1].timestamp > timedelta(
            minutes=gap_minutes
        ):
            groups.append([signal])
        else:
            groups[-1].append(signal)
    events = []
    for group in groups:
        peak = max(group, key=lambda signal: abs(signal.mad_score))
        events.append(
            {
                "start": group[0].timestamp,
                "end": group[-1].timestamp,
                "peak": peak,
            }
        )
    return events
