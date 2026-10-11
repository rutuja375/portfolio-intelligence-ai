
from collections.abc import Sequence


def validate_bars(bars: Sequence) -> None:
    """Validate basic structural integrity of OHLCV bars."""
    previous_timestamp = None

    for bar in bars:
        if bar.low <= 0:
            raise ValueError("Low price must be positive")

        if not (
            bar.low <= bar.open <= bar.high
            and bar.low <= bar.close <= bar.high
        ):
            raise ValueError(
                f"Invalid OHLC prices at {bar.timestamp}"
            )

        if bar.volume < 0:
            raise ValueError(
                f"Negative volume at {bar.timestamp}"
            )

        if (
            previous_timestamp is not None
            and bar.timestamp <= previous_timestamp
        ):
            raise ValueError(
                f"Unsorted or duplicate timestamp: {bar.timestamp}"
            )

        previous_timestamp = bar.timestamp
