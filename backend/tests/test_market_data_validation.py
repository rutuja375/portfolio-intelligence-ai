
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.market_data.validation import validate_bars

BASE_TIME = datetime(2026, 10, 5, 13, 30, tzinfo=UTC)


def make_bar(
    minute=0,
    open_price=100.0,
    high=105.0,
    low=95.0,
    close=102.0,
    volume=1000,
):
    return SimpleNamespace(
        timestamp=BASE_TIME + timedelta(minutes=minute),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_valid_bars():
    bars = [make_bar(minute=0), make_bar(minute=1)]
    validate_bars(bars)


def test_invalid_price():
    bar = make_bar(open_price=110.0)

    with pytest.raises(ValueError, match="Invalid OHLC"):
        validate_bars([bar])


def test_negative_volume():
    bar = make_bar(volume=-100)

    with pytest.raises(ValueError, match="Negative volume"):
        validate_bars([bar])


def test_duplicate_timestamp():
    bars = [make_bar(minute=0), make_bar(minute=0)]

    with pytest.raises(ValueError, match="Unsorted or duplicate"):
        validate_bars(bars)


def test_unsorted_timestamps():
    bars = [make_bar(minute=2), make_bar(minute=1)]

    with pytest.raises(ValueError, match="Unsorted or duplicate"):
        validate_bars(bars)


def test_nonpositive_price():
    bar = make_bar(low=0)

    with pytest.raises(ValueError, match="Low price must be positive"):
        validate_bars([bar])
