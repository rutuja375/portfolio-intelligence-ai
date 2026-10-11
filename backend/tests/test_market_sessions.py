
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.market_data.sessions import (
    filter_regular_session,
    is_regular_session,
)


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        # Summer: New York uses UTC-4
        (datetime(2026, 7, 6, 13, 29, tzinfo=UTC), False),
        (datetime(2026, 7, 6, 13, 30, tzinfo=UTC), True),
        (datetime(2026, 7, 6, 19, 59, tzinfo=UTC), True),
        (datetime(2026, 7, 6, 20, 0, tzinfo=UTC), False),

        # Winter: New York uses UTC-5
        (datetime(2026, 1, 5, 14, 30, tzinfo=UTC), True),
        (datetime(2026, 1, 5, 21, 0, tzinfo=UTC), False),

        # Weekend
        (datetime(2026, 7, 4, 15, 0, tzinfo=UTC), False),

        # Christmas Day: exchange closed
        (datetime(2026, 12, 25, 15, 0, tzinfo=UTC), False),

        # Thanksgiving Friday: 1 PM ET early close
        (datetime(2026, 11, 27, 17, 59, tzinfo=UTC), True),
        (datetime(2026, 11, 27, 18, 0, tzinfo=UTC), False),

        # Christmas Eve: 1 PM ET early close
        (datetime(2026, 12, 24, 17, 59, tzinfo=UTC), True),
        (datetime(2026, 12, 24, 18, 0, tzinfo=UTC), False),
    ],
)
def test_regular_session_boundaries(timestamp, expected):
    assert is_regular_session(timestamp) is expected


def test_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone"):
        is_regular_session(datetime(2026, 7, 6, 13, 30))


def test_filter_regular_session():
    bars = [
        SimpleNamespace(
            timestamp=datetime(2026, 7, 6, 13, 29, tzinfo=UTC)
        ),
        SimpleNamespace(
            timestamp=datetime(2026, 7, 6, 13, 30, tzinfo=UTC)
        ),
        SimpleNamespace(
            timestamp=datetime(2026, 7, 6, 20, 0, tzinfo=UTC)
        ),
    ]

    filtered = filter_regular_session(bars)

    assert len(filtered) == 1
    assert filtered[0] is bars[1]


def test_filter_excludes_holiday():
    bars = [
        SimpleNamespace(
            timestamp=datetime(2026, 12, 25, 15, 0, tzinfo=UTC)
        )
    ]

    assert filter_regular_session(bars) == []
