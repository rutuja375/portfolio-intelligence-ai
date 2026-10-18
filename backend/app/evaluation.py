from dataclasses import dataclass
from datetime import datetime

from app.evidence.models import RankedEvidence
from app.explanations.grounding import Explanation


@dataclass(frozen=True)
class EvaluationResult:
    valid_citation_rate: float
    temporal_eligibility_rate: float
    abstention_expected: bool
    abstention_correct: bool
    semantic_relevance_coverage: float
    sentiment_coverage: float


def evaluate_explanation(
    explanation: Explanation,
    evidence: list[RankedEvidence],
    event_time: datetime,
    *,
    context_supported: bool = False,
) -> EvaluationResult:
    valid = {f"E{index}" for index in range(1, len(evidence) + 1)}
    citation_rate = (
        sum(citation in valid for citation in explanation.citations) / len(explanation.citations)
        if explanation.citations
        else (1.0 if explanation.abstained or context_supported else 0.0)
    )
    temporal_rate = (
        sum(item.article.published_at <= event_time for item in evidence) / len(evidence)
        if evidence
        else 1.0
    )
    expected = not evidence and not context_supported
    semantic_coverage = (
        sum(item.semantic_score is not None for item in evidence) / len(evidence)
        if evidence
        else 0.0
    )
    sentiment_coverage = (
        sum(item.sentiment is not None for item in evidence) / len(evidence)
        if evidence
        else 0.0
    )
    return EvaluationResult(
        valid_citation_rate=citation_rate,
        temporal_eligibility_rate=temporal_rate,
        abstention_expected=expected,
        abstention_correct=explanation.abstained == expected,
        semantic_relevance_coverage=semantic_coverage,
        sentiment_coverage=sentiment_coverage,
    )
