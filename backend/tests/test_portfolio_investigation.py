from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.evidence.models import Article
from app.portfolio_investigation import investigate_portfolio_history


def bars(symbol: str, values: list[float]):
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        SimpleNamespace(
            symbol=symbol,
            timestamp=start + timedelta(minutes=index),
            open=value,
            high=value,
            low=value,
            close=value,
            volume=100,
        )
        for index, value in enumerate(values)
    ]


def test_portfolio_investigation_returns_dashboard_payload():
    prices = [100, 100.1, 100, 100.2, 100, 100.1, 106]
    event_time = datetime(2026, 1, 2, 14, 36, tzinfo=UTC)
    result = investigate_portfolio_history(
        weights={"AAPL": 1.0},
        bars_by_symbol={"AAPL": bars("AAPL", prices)},
        articles=[
            Article(
                id="one",
                title="Apple publishes an update",
                url="https://example.com/one",
                source="Example",
                published_at=event_time - timedelta(minutes=1),
                symbols=("AAPL",),
            )
        ],
        benchmark_bars=bars("SPY", [100] * 7),
        sector_bars=bars("QQQ", [100] * 7),
        window=5,
        threshold=3,
    )
    assert result["status"] == "completed"
    assert result["summary"]["anomalies"] == 1
    assert result["events"][0]["primary_symbol"] == "AAPL"
    assert result["events"][0]["explanation"]["citations"] == ("E1",)
