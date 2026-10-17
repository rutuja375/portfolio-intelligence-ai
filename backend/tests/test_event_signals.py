from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.analytics.event_signals import (
    calculate_multi_window_signals,
    group_confirmed_events,
)


def _bars(symbol: str, prices: list[float], volumes: list[float]):
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        SimpleNamespace(
            symbol=symbol,
            timestamp=start + timedelta(minutes=index),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=volumes[index],
        )
        for index, price in enumerate(prices)
    ]


def test_confirms_five_minute_event_when_return_and_volume_agree():
    prices = [100 + (index % 2) * 0.02 for index in range(45)]
    prices.extend([101, 102, 103, 104, 105])
    volumes = [100] * 45 + [500] * 5
    signals = calculate_multi_window_signals(
        {"AAPL": _bars("AAPL", prices, volumes)},
        {"AAPL": 1.0},
        horizons=(1, 5),
        confirmation_horizon=5,
        baseline_window=6,
        threshold=2,
        volatility_threshold=2,
        volume_threshold=1.5,
    )
    confirmed = [signal for signal in signals if signal.confirmed]
    assert confirmed
    assert all(signal.horizon_minutes == 5 for signal in confirmed)
    assert confirmed[-1].volume_ratio >= 4


def test_rejects_price_spike_without_abnormal_volume():
    prices = [100 + (index % 2) * 0.02 for index in range(45)]
    prices.extend([101, 102, 103, 104, 105])
    signals = calculate_multi_window_signals(
        {"AAPL": _bars("AAPL", prices, [100] * len(prices))},
        {"AAPL": 1.0},
        horizons=(1, 5),
        confirmation_horizon=5,
        baseline_window=6,
        threshold=2,
        volatility_threshold=2,
        volume_threshold=1.5,
    )
    assert any(abs(signal.mad_score) >= 2 for signal in signals)
    assert not any(signal.confirmed for signal in signals)


def test_groups_nearby_confirmations_into_one_event():
    prices = [100 + (index % 2) * 0.02 for index in range(45)]
    prices.extend([101, 102, 103, 104, 105, 106])
    volumes = [100] * 45 + [500] * 6
    signals = calculate_multi_window_signals(
        {"AAPL": _bars("AAPL", prices, volumes)},
        {"AAPL": 1.0},
        horizons=(5,),
        confirmation_horizon=5,
        baseline_window=6,
        threshold=2,
        volatility_threshold=2,
        volume_threshold=1.5,
    )
    events = group_confirmed_events(signals)
    assert len(events) == 1
    assert events[0]["start"] <= events[0]["peak"].timestamp <= events[0]["end"]
