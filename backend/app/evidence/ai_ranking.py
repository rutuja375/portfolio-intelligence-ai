import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.nlp.finbert import FinBertSentiment


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class Reranker(Protocol):
    def score(self, query: str, documents: list[str]) -> list[float]: ...


class SentimentModel(Protocol):
    def score(self, text: str) -> float: ...


class SentenceTransformerEmbedder:
    """Lazy local semantic encoder; model files are downloaded only when enabled."""

    MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model=None) -> None:
        self._model = model

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.MODEL)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        values = self._load().encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in values]


class CrossEncoderEvidenceReranker:
    """Lazy cross-encoder for query/article relevance scoring."""

    MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model=None) -> None:
        self._model = model

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.MODEL)
        return self._model

    def score(self, query: str, documents: list[str]) -> list[float]:
        raw = self._load().predict([(query, document) for document in documents])
        return [1.0 / (1.0 + math.exp(-float(value))) for value in raw]


@dataclass(frozen=True)
class EvidenceAI:
    embedder: Embedder
    reranker: Reranker
    sentiment: SentimentModel


@lru_cache(maxsize=1)
def local_evidence_ai() -> EvidenceAI:
    return EvidenceAI(
        embedder=SentenceTransformerEmbedder(),
        reranker=CrossEncoderEvidenceReranker(),
        sentiment=FinBertSentiment(),
    )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


FINANCIAL_EVENTS = {
    "earnings": ("earnings", "revenue", "profit", "quarter", "results"),
    "guidance": ("guidance", "forecast", "outlook", "expects"),
    "analyst_action": ("upgrade", "downgrade", "price target", "rating"),
    "corporate_action": ("merger", "acquisition", "buyback", "dividend", "split"),
    "regulation": ("regulation", "regulator", "antitrust", "investigation", "lawsuit"),
    "macro": ("inflation", "interest rate", "federal reserve", "jobs report", "tariff"),
    "product": ("launch", "product", "approval", "recall", "shipment"),
}


def extract_financial_events(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(
        event
        for event, phrases in FINANCIAL_EVENTS.items()
        if any(phrase in lowered for phrase in phrases)
    )
