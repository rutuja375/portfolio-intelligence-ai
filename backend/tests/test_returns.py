
import pytest
from app.analytics.returns import calculate_simple_return


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (100.0, 105.0, 0.05),
        (100.0, 95.0, -0.05),
        (100.0, 100.0, 0.0),
        (200.0, 210.0, 0.05),
    ],
)
def test_simple_returns(previous, current, expected):
    result = calculate_simple_return(previous, current)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    ("previous", "current"),
    [
        (0.0, 100.0),
        (-100.0, 100.0),
        (100.0, 0.0),
        (100.0, -5.0),
    ],
)
def test_invalid_prices(previous, current):
    with pytest.raises(ValueError, match="Prices must be positive"):
        calculate_simple_return(previous, current)
