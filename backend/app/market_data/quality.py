from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from itertools import pairwise


@dataclass(frozen=True)
class DataQualityReport:
    observed_timestamps: int
    complete_timestamps: int
    missing_prices: dict[str, int]
    duplicate_timestamps: dict[str, int]
    stale_intervals: dict[str, int]
    coverage: float
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def assess_data_quality(
    bars_by_symbol: dict[str, list],
    aligned_prices: dict[datetime, dict[str, float | None]],
) -> DataQualityReport:
    """Summarize gaps and suspicious observations without inventing prices."""
    symbols = tuple(bars_by_symbol)
    missing = {
        symbol: sum(prices.get(symbol) is None for prices in aligned_prices.values())
        for symbol in symbols
    }
    duplicates: dict[str, int] = {}
    stale: dict[str, int] = {}
    for symbol, bars in bars_by_symbol.items():
        timestamps = [bar.timestamp for bar in bars]
        duplicates[symbol] = len(timestamps) - len(set(timestamps))
        ordered = sorted(bars, key=lambda bar: bar.timestamp)
        stale[symbol] = sum(
            current.timestamp - previous.timestamp == timedelta(minutes=1)
            and current.close == previous.close
            and getattr(current, "volume", 0) == 0
            for previous, current in pairwise(ordered)
        )

    observed = len(aligned_prices)
    complete = sum(
        bool(symbols) and all(prices.get(symbol) is not None for symbol in symbols)
        for prices in aligned_prices.values()
    )
    warnings = []
    if observed == 0:
        warnings.append("No market observations were returned.")
    if any(missing.values()):
        warnings.append("Some timestamps are missing one or more holding prices.")
    if any(duplicates.values()):
        warnings.append("Duplicate source timestamps were detected.")
    if any(stale.values()):
        warnings.append("Zero-volume unchanged-price intervals were detected.")
    return DataQualityReport(
        observed_timestamps=observed,
        complete_timestamps=complete,
        missing_prices=missing,
        duplicate_timestamps=duplicates,
        stale_intervals=stale,
        coverage=complete / observed if observed else 0.0,
        warnings=tuple(warnings),
    )
