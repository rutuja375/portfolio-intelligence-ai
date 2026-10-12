
import os
from datetime import UTC, datetime, timedelta
from itertools import pairwise

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

from app.analytics.returns import calculate_simple_return
from app.market_data.sessions import filter_regular_session
from app.market_data.validation import validate_bars


def fetch_regular_session_bars(
    client: StockHistoricalDataClient,
    symbols: list[str],
    start: datetime,
    end: datetime,
) -> dict:
    """Retrieve, validate, and filter minute bars for multiple stocks."""

    if not symbols:
        raise ValueError("At least one stock symbol is required")

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Minute,
        start=start,
        end=end,
        feed="iex",
    )

    response = client.get_stock_bars(request)

    regular_bars_by_symbol = {}

    for symbol in symbols:
        bars = response.data.get(symbol, [])

        validate_bars(bars)

        regular_bars = filter_regular_session(bars)
        validate_bars(regular_bars)

        regular_bars_by_symbol[symbol] = regular_bars

    return regular_bars_by_symbol


def main():
    # Load API credentials from the project's .env file.
    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca API credentials in .env")

    # Historical data client; does not place trades.
    client = StockHistoricalDataClient(api_key, secret_key)

    # Request a completed historical window.
    end = datetime.now(UTC) - timedelta(days=1)
    start = end - timedelta(days=7)

    symbols = ["NVDA", "AAPL", "MSFT"]

    # Retrieve validated, regular-session data.
    regular_bars_by_symbol = fetch_regular_session_bars(
        client=client,
        symbols=symbols,
        start=start,
        end=end,
    )

    print("\nMulti-stock regular-session data summary:")

    for symbol in symbols:
        print(
            f"{symbol}: "
            f"{len(regular_bars_by_symbol[symbol])} regular-session bars"
        )

    # Display the first five NVDA bars.
    nvda_bars = regular_bars_by_symbol["NVDA"]

    print("\nFirst five regular-session NVDA bars:")

    for bar in nvda_bars[:5]:
        print(
            f"{bar.timestamp} | "
            f"Open: {bar.open} | "
            f"High: {bar.high} | "
            f"Low: {bar.low} | "
            f"Close: {bar.close} | "
            f"Volume: {bar.volume}"
        )

    # Calculate returns between consecutive observed minutes.
    print("\nFirst five NVDA minute-level returns:")

    printed = 0

    for previous_bar, current_bar in pairwise(nvda_bars):
        time_difference = (
            current_bar.timestamp - previous_bar.timestamp
        )

        # Skip missing minutes and overnight gaps.
        if time_difference != timedelta(minutes=1):
            continue

        stock_return = calculate_simple_return(
            previous_bar.close,
            current_bar.close,
        )

        print(
            f"{current_bar.timestamp} | "
            f"Return: {stock_return:.4%}"
        )

        printed += 1

        if printed == 5:
            break

    print("\nMarket data retrieval and return calculation completed!")


if __name__ == "__main__":
    main()
