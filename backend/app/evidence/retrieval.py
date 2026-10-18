from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from typing import Protocol

from app.evidence.ai_ranking import (
    EvidenceAI,
    cosine_similarity,
    extract_financial_events,
)
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
    ai: EvidenceAI | None = None,
    movement_direction: int = 0,
) -> list[RankedEvidence]:
    """Apply temporal safeguards, then optionally run hybrid AI evidence ranking."""
    if event_time.tzinfo is None or event_time.utcoffset() is None:
        raise ValueError("Event time must be timezone-aware")
    symbol_set = {symbol.upper() for symbol in symbols}
    query_tokens = _tokens(query) | {symbol.lower() for symbol in symbol_set}
    candidates = []
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
        candidates.append((article, score, reasons))

    semantic_scores: list[float | None] = [None] * len(candidates)
    reranker_scores: list[float | None] = [None] * len(candidates)
    sentiments: list[float | None] = [None] * len(candidates)
    documents = [f"{article.title}. {article.summary}" for article, _, _ in candidates]
    if ai is not None and documents:
        vectors = ai.embedder.encode([query, *documents])
        semantic_scores = [cosine_similarity(vectors[0], vector) for vector in vectors[1:]]
        reranker_scores = ai.reranker.score(query, documents)
        sentiments = [ai.sentiment.score(document) for document in documents]

    ranked = []
    for index, (article, base_score, reasons) in enumerate(candidates):
        semantic = semantic_scores[index]
        reranker = reranker_scores[index]
        sentiment = sentiments[index]
        score = base_score
        if semantic is not None:
            score += 2.0 * max(0.0, semantic)
            reasons.append("semantic_match")
        if reranker is not None:
            score += 2.0 * max(0.0, reranker)
            reasons.append("ai_reranked")
        if sentiment is not None and movement_direction:
            alignment = sentiment * movement_direction
            score += 0.25 * alignment
            reasons.append("sentiment_context")
        ranked.append(
            RankedEvidence(
                article=article,
                score=score,
                reasons=tuple(reasons),
                sentiment=sentiment,
                semantic_score=semantic,
                reranker_score=reranker,
                event_tags=extract_financial_events(documents[index]),
            )
        )
    return sorted(
        ranked,
        key=lambda evidence: (-evidence.score, -evidence.article.published_at.timestamp()),
    )[:limit]
