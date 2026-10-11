
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


def main():
    # Load API credentials from the project's .env file.
    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca API credentials in .env")

    # Retrieve historical market data without placing trades.
    client = StockHistoricalDataClient(api_key, secret_key)

    end = datetime.now(UTC) - timedelta(days=1)
    start = end - timedelta(days=7)

    request = StockBarsRequest(
        symbol_or_symbols="NVDA",
        timeframe=TimeFrame.Minute,
        start=start,
        end=end,
        feed="iex",
    )

    response = client.get_stock_bars(request)
    bars = response.data.get("NVDA", [])

    # Validate and filter the retrieved bars.
    validate_bars(bars)
    print("Market data validation passed!")

    regular_bars = filter_regular_session(bars)
    validate_bars(regular_bars)

    print(f"Total retrieved bars: {len(bars)}")
    print(f"Regular-session bars: {len(regular_bars)}")
    print(f"Excluded bars: {len(bars) - len(regular_bars)}")

    # Display the first five regular-session OHLCV bars.
    print("\nFirst five regular-session NVDA bars:")

    for bar in regular_bars[:5]:
        print(
            f"{bar.timestamp} | "
            f"Open: {bar.open} | "
            f"High: {bar.high} | "
            f"Low: {bar.low} | "
            f"Close: {bar.close} | "
            f"Volume: {bar.volume}"
        )

    # Calculate returns for consecutive one-minute bars.
    print("\nFirst five NVDA minute-level returns:")

    printed = 0

    for previous_bar, current_bar in pairwise(regular_bars):
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

    print("\nReturn calculation completed!")


if __name__ == "__main__":
    main()
