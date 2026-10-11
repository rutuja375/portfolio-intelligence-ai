
import os
from datetime import UTC, datetime, timedelta

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

from app.market_data.validation import validate_bars


def main():
    # Load API credentials from the project's .env file.
    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca API credentials in .env")

    # This client retrieves market data; it does not place trades.
    client = StockHistoricalDataClient(api_key, secret_key)

    # Request a completed historical window.
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

    validate_bars(bars)
    print("Market data validation passed!")

    print(f"Retrieved {len(bars)} NVDA minute bars")

    for bar in bars[:5]:
        print(
            f"{bar.timestamp} | "
            f"Open: {bar.open} | "
            f"High: {bar.high} | "
            f"Low: {bar.low} | "
            f"Close: {bar.close} | "
            f"Volume: {bar.volume}"
        )


if __name__ == "__main__":
    main()
