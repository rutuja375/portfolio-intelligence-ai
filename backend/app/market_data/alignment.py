
from datetime import datetime


def align_bars_by_timestamp(
    bars_by_symbol: dict[str, list],
) -> dict[datetime, dict[str, float | None]]:
    """Align stock closing prices by their observed timestamps."""
    symbols = list(bars_by_symbol)

    timestamps = sorted(
        {
            bar.timestamp
            for bars in bars_by_symbol.values()
            for bar in bars
        }
    )

    aligned = {
        timestamp: {symbol: None for symbol in symbols}
        for timestamp in timestamps
    }

    for symbol, bars in bars_by_symbol.items():
        for bar in bars:
            aligned[bar.timestamp][symbol] = bar.close

    return aligned
