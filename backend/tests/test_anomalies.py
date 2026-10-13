from datetime import UTC, datetime, timedelta

import pytest
from app.analytics.anomalies import (
    contextualize_return,
    detect_rolling_anomalies,
    estimate_beta,
)


def test_rolling_detector_uses_only_prior_observations():
    start = datetime(2026, 1, 2, tzinfo=UTC)
    values = [0.0, 0.001, -0.001, 0.002, -0.002, 0.001, 0.05]
    result = detect_rolling_anomalies(
        [(start + timedelta(minutes=i), value) for i, value in enumerate(values)],
        window=6,
    )
    assert len(result) == 1
    assert result[0].direction == "up"
    assert result[0].timestamp == start + timedelta(minutes=6)


def test_market_context_uses_estimated_beta():
    assert estimate_beta([0.01, 0.02, 0.03], [0.005, 0.01, 0.015]) == pytest.approx(2)
    context = contextualize_return(
        0.03,
        0.01,
        sector_return=0.02,
        asset_history=[0.01, 0.02, 0.03],
        market_history=[0.005, 0.01, 0.015],
    )
    assert context.market_adjusted_return == pytest.approx(0.01)
    assert context.sector_adjusted_return == pytest.approx(0.01)
