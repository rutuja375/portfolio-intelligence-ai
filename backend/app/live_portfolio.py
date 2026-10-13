import os
from datetime import datetime

from alpaca.data.historical import NewsClient, StockHistoricalDataClient

from app.evidence.alpaca_news import AlpacaNewsProvider
from app.market_data.alpaca_provider import fetch_regular_session_bars
from app.portfolio_investigation import investigate_portfolio_history


def run_live_portfolio_investigation(
    *,
    weights: dict[str, float],
    start: datetime,
    end: datetime,
    window: int = 30,
    threshold: float = 3.5,
) -> dict:
    """Retrieve Alpaca IEX bars/news and run a historical portfolio investigation."""
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca API credentials in .env")
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Start and end must include timezone information")
    if start >= end:
        raise ValueError("Start must be before end")

    symbols = list(weights)
    market_client = StockHistoricalDataClient(api_key, secret_key)
    requested_symbols = list(dict.fromkeys([*symbols, "SPY", "QQQ"]))
    all_bars = fetch_regular_session_bars(
        market_client, requested_symbols, start, end
    )
    bars_by_symbol = {symbol: all_bars[symbol] for symbol in symbols}
    news = list(
        AlpacaNewsProvider(NewsClient(api_key, secret_key)).search(
            symbols, start, end
        )
    )
    return investigate_portfolio_history(
        weights=weights,
        bars_by_symbol=bars_by_symbol,
        articles=news,
        benchmark_bars=all_bars["SPY"],
        sector_bars=all_bars["QQQ"],
        window=window,
        threshold=threshold,
    )
