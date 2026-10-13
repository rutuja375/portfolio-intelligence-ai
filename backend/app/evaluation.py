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


def evaluate_explanation(
    explanation: Explanation,
    evidence: list[RankedEvidence],
    event_time: datetime,
) -> EvaluationResult:
    valid = {f"E{index}" for index in range(1, len(evidence) + 1)}
    citation_rate = (
        sum(citation in valid for citation in explanation.citations) / len(explanation.citations)
        if explanation.citations
        else (1.0 if explanation.abstained else 0.0)
    )
    temporal_rate = (
        sum(item.article.published_at <= event_time for item in evidence) / len(evidence)
        if evidence
        else 1.0
    )
    expected = not evidence
    return EvaluationResult(
        valid_citation_rate=citation_rate,
        temporal_eligibility_rate=temporal_rate,
        abstention_expected=expected,
        abstention_correct=explanation.abstained == expected,
    )
