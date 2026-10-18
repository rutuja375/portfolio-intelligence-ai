from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""
    symbols: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("Article publication time must be timezone-aware")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("Article URL must be absolute")


@dataclass(frozen=True)
class RankedEvidence:
    article: Article
    score: float
    reasons: tuple[str, ...]
    sentiment: float | None = None
    semantic_score: float | None = None
    reranker_score: float | None = None
    event_tags: tuple[str, ...] = ()
