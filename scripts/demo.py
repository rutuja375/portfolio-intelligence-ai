"""Offline control-flow demo; values are labeled fixtures, not market prices."""

import json
from datetime import UTC, datetime, timedelta

from app.evidence.models import Article
from app.investigation import investigate_movement


def main() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    returns = [0, 0.001, -0.001, 0.002, -0.002, 0.001, 0.05]
    event_time = start + timedelta(minutes=6)
    result = investigate_movement(
        symbol="DEMO",
        observations=[
            (start + timedelta(minutes=index), value)
            for index, value in enumerate(returns)
        ],
        articles=[
            Article(
                id="demo-evidence",
                title="Illustrative company update",
                url="https://example.com/illustrative-evidence",
                source="Offline demo fixture",
                published_at=event_time - timedelta(minutes=1),
                symbols=("DEMO",),
            )
        ],
        window=6,
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
