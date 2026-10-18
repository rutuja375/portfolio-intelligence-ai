from datetime import UTC, datetime, timedelta

from app.evidence.ai_ranking import EvidenceAI
from app.evidence.models import Article, RankedEvidence
from app.evidence.retrieval import rank_evidence
from app.explanations.grounding import explain_with_evidence


def article(identifier, published_at, *, symbols=("AAPL",)):
    return Article(
        id=identifier,
        title="Apple updates outlook",
        url=f"https://example.com/{identifier}",
        source="Example Wire",
        published_at=published_at,
        symbols=symbols,
    )


def test_ranking_excludes_future_news():
    event_time = datetime(2026, 1, 2, 15, 0, tzinfo=UTC)
    ranked = rank_evidence(
        [
            article("before", event_time - timedelta(minutes=10)),
            article("after", event_time + timedelta(seconds=1)),
        ],
        symbols=["AAPL"],
        event_time=event_time,
        query="outlook",
    )
    assert [item.article.id for item in ranked] == ["before"]


def test_explainer_abstains_without_evidence():
    result = explain_with_evidence({"symbol": "AAPL"}, [])
    assert result.abstained is True
    assert result.citations == ()


def test_explainer_rejects_unknown_model_citation():
    evidence = RankedEvidence(
        article=article("one", datetime(2026, 1, 2, 14, 0, tzinfo=UTC)),
        score=1,
        reasons=("symbol_match",),
    )

    class BadGenerator:
        def generate(self, **kwargs):
            return '{"summary":"Claim [E9]","confidence":"high"}'

    result = explain_with_evidence({}, [evidence], BadGenerator())
    assert result.abstained is True


def test_hybrid_ranking_uses_semantics_reranker_and_sentiment():
    event_time = datetime(2026, 1, 2, 15, 0, tzinfo=UTC)

    class Embedder:
        def encode(self, texts):
            return [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]

    class Reranker:
        def score(self, query, documents):
            return [0.9, 0.1]

    class Sentiment:
        def score(self, text):
            return 0.8 if "guidance" in text.lower() else -0.2

    relevant = Article(
        id="relevant",
        title="Chipmaker raises guidance after strong demand",
        url="https://example.com/relevant",
        source="Example Wire",
        published_at=event_time - timedelta(minutes=20),
        summary="Revenue outlook improved.",
        symbols=("NVDA",),
    )
    weak = Article(
        id="weak",
        title="Unrelated market diary",
        url="https://example.com/weak",
        source="Example Wire",
        published_at=event_time - timedelta(minutes=5),
        symbols=("NVDA",),
    )
    ranked = rank_evidence(
        [relevant, weak],
        symbols=["NVDA"],
        event_time=event_time,
        query="NVDA earnings guidance",
        ai=EvidenceAI(Embedder(), Reranker(), Sentiment()),
        movement_direction=1,
    )
    assert ranked[0].article.id == "relevant"
    assert ranked[0].semantic_score is not None
    assert "ai_reranked" in ranked[0].reasons
    assert ranked[0].event_tags == ("earnings", "guidance")
