from datetime import UTC, datetime, timedelta

import pytest
from app.analytics.performance import compound_returns, cumulative_performance


def test_cumulative_performance_compounds_in_time_order():
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    points = cumulative_performance(
        [
            {"timestamp": start + timedelta(minutes=1), "portfolio_return": -0.1},
            {"timestamp": start, "portfolio_return": 0.1},
        ]
    )
    assert points[-1].cumulative_return == pytest.approx(-0.01)
    assert points[-1].wealth_index == pytest.approx(0.99)


def test_compound_returns_rejects_total_loss():
    with pytest.raises(ValueError, match="-100%"):
        compound_returns([0.1, -1.0])
