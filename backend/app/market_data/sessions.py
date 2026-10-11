
from datetime import UTC, datetime

import exchange_calendars as xcals
import pandas as pd

CALENDAR = xcals.get_calendar("XNYS")


def is_regular_session(timestamp: datetime) -> bool:
    """Return True if a minute bar starts during an XNYS session."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timestamp must include timezone information")

    utc_timestamp = pd.Timestamp(timestamp.astimezone(UTC))
    session_date = utc_timestamp.tz_convert(
        "America/New_York"
    ).date()

    if not CALENDAR.is_session(session_date):
        return False

    market_open = CALENDAR.session_open(session_date)
    market_close = CALENDAR.session_close(session_date)

    return bool(market_open <= utc_timestamp < market_close)


def filter_regular_session(bars):
    """Return only bars inside scheduled regular trading sessions."""
    return [
        bar for bar in bars
        if is_regular_session(bar.timestamp)
    ]
