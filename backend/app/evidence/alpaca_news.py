from collections.abc import Iterable, Sequence
from datetime import datetime

from app.evidence.models import Article


class AlpacaNewsProvider:
    """Adapter around Alpaca's historical news client."""

    def __init__(self, client) -> None:
        self.client = client

    def search(
        self, symbols: Sequence[str], start: datetime, end: datetime
    ) -> Iterable[Article]:
        from alpaca.data.requests import NewsRequest

        response = self.client.get_news(
            NewsRequest(symbols=",".join(symbols), start=start, end=end)
        )
        for item in response.data.get("news", []):
            yield Article(
                id=str(item.id),
                title=item.headline,
                url=item.url,
                source=item.source,
                published_at=item.created_at,
                summary=item.summary or "",
                symbols=tuple(item.symbols or ()),
            )
