from datetime import UTC, datetime, timedelta

from app.evidence.models import Article
from app.investigation import investigate_movement


def test_end_to_end_investigation_is_time_safe_and_cited():
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    values = [0, 0.001, -0.001, 0.002, -0.002, 0.001, 0.05]
    event_time = start + timedelta(minutes=6)
    articles = [
        Article(
            id="eligible",
            title="Apple releases outlook",
            url="https://example.com/eligible",
            source="Example Wire",
            published_at=event_time - timedelta(minutes=1),
            symbols=("AAPL",),
        ),
        Article(
            id="future",
            title="Later analysis",
            url="https://example.com/future",
            source="Example Wire",
            published_at=event_time + timedelta(minutes=1),
            symbols=("AAPL",),
        ),
    ]
    result = investigate_movement(
        symbol="AAPL",
        observations=[(start + timedelta(minutes=i), value) for i, value in enumerate(values)],
        articles=articles,
        window=6,
    )
    event = result["events"][0]
    assert [item["title"] for item in event["evidence"]] == ["Apple releases outlook"]
    assert event["explanation"]["citations"] == ("E1",)
    assert event["evaluation"]["temporal_eligibility_rate"] == 1.0
