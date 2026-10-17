from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.evidence.models import Article
from app.portfolio_investigation import investigate_portfolio_history


def bars(symbol: str, values: list[float], volumes: list[float] | None = None):
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        SimpleNamespace(
            symbol=symbol,
            timestamp=start + timedelta(minutes=index),
            open=value,
            high=value,
            low=value,
            close=value,
            volume=(volumes or [100] * len(values))[index],
        )
        for index, value in enumerate(values)
    ]


def test_portfolio_investigation_returns_dashboard_payload():
    prices = [100 + (index % 2) * 0.02 for index in range(45)]
    prices.extend([101, 102, 103, 104, 106])
    volumes = [100] * 45 + [500] * 5
    event_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = investigate_portfolio_history(
        weights={"AAPL": 1.0},
        bars_by_symbol={"AAPL": bars("AAPL", prices, volumes)},
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
        benchmark_bars=bars("SPY", [100] * len(prices)),
        sector_bars=bars("QQQ", [100] * len(prices)),
        window=6,
        threshold=2,
        horizons=(1, 5),
        volatility_threshold=2,
        volume_threshold=1.5,
    )
    assert result["status"] == "completed"
    assert result["summary"]["anomalies"] == 1
    assert result["events"][0]["primary_symbol"] == "AAPL"
    assert result["events"][0]["confirmation"]["confirmed"] is True
    assert result["events"][0]["explanation"]["citations"] == ("E1",)


def test_uses_market_context_when_company_evidence_is_missing():
    prices = [100 + (index % 2) * 0.02 for index in range(45)]
    prices.extend([101, 102, 103, 104, 106])
    market = [100] * 45 + [100.5, 101, 101.5, 102, 103]
    result = investigate_portfolio_history(
        weights={"AAPL": 1.0},
        bars_by_symbol={
            "AAPL": bars("AAPL", prices, [100] * 45 + [500] * 5)
        },
        articles=[],
        benchmark_bars=bars("SPY", market),
        sector_bars=bars("QQQ", market),
        window=6,
        threshold=2,
        horizons=(1, 5),
        volatility_threshold=2,
        volume_threshold=1.5,
    )
    event = result["events"][0]
    assert "market-wide conditions" in event["explanation"]["summary"]
    assert event["explanation"]["abstained"] is False
    assert event["evaluation"]["abstention_correct"] is True
