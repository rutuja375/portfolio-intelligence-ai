from datetime import UTC, datetime, timedelta

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
