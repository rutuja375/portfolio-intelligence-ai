from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from typing import Protocol

from app.evidence.models import Article, RankedEvidence


class NewsProvider(Protocol):
    def search(
        self, symbols: Sequence[str], start: datetime, end: datetime
    ) -> Iterable[Article]: ...


def _tokens(text: str) -> set[str]:
    return {token.strip(".,:;!?()[]{}\"'").lower() for token in text.split() if token}


def rank_evidence(
    articles: Iterable[Article],
    *,
    symbols: Sequence[str],
    event_time: datetime,
    query: str = "",
    lookback: timedelta = timedelta(hours=24),
    limit: int = 8,
) -> list[RankedEvidence]:
    """Rank only evidence published by the event time to prevent look-ahead bias."""
    if event_time.tzinfo is None or event_time.utcoffset() is None:
        raise ValueError("Event time must be timezone-aware")
    symbol_set = {symbol.upper() for symbol in symbols}
    query_tokens = _tokens(query) | {symbol.lower() for symbol in symbol_set}
    ranked = []
    for article in articles:
        age = event_time - article.published_at
        if age < timedelta(0) or age > lookback:
            continue
        article_symbols = {symbol.upper() for symbol in article.symbols}
        symbol_overlap = len(symbol_set & article_symbols)
        text_tokens = _tokens(f"{article.title} {article.summary}")
        lexical_overlap = len(query_tokens & text_tokens)
        recency = max(0.0, 1 - age.total_seconds() / lookback.total_seconds())
        score = 3.0 * symbol_overlap + lexical_overlap + recency
        reasons = []
        if symbol_overlap:
            reasons.append("symbol_match")
        if lexical_overlap:
            reasons.append("keyword_match")
        reasons.append("published_before_event")
        ranked.append(RankedEvidence(article=article, score=score, reasons=tuple(reasons)))
    return sorted(
        ranked,
        key=lambda evidence: (-evidence.score, evidence.article.published_at),
    )[:limit]
