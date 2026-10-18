import json
import re
from dataclasses import dataclass
from typing import Protocol

from app.evidence.models import RankedEvidence

CITATION_PATTERN = re.compile(r"\[(E\d+)\]")


class TextGenerator(Protocol):
    def generate(self, *, system: str, prompt: str) -> str: ...


class OpenAIResponsesGenerator:
    """Optional OpenAI Responses API adapter; the API key stays in the environment."""

    def __init__(self, model: str = "gpt-5-mini", client=None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model

    def generate(self, *, system: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model, instructions=system, input=prompt
        )
        return response.output_text


@dataclass(frozen=True)
class Explanation:
    summary: str
    confidence: str
    citations: tuple[str, ...]
    limitations: tuple[str, ...]
    abstained: bool


def _evidence_payload(evidence: list[RankedEvidence]) -> list[dict]:
    return [
        {
            "citation": f"E{index}",
            "title": item.article.title,
            "source": item.article.source,
            "published_at": item.article.published_at.isoformat(),
            "url": item.article.url,
            "summary": item.article.summary,
            "relevance_score": item.score,
            "semantic_score": item.semantic_score,
            "reranker_score": item.reranker_score,
            "financial_sentiment": item.sentiment,
            "event_tags": item.event_tags,
        }
        for index, item in enumerate(evidence, start=1)
    ]


def explain_with_evidence(
    event: dict,
    evidence: list[RankedEvidence],
    generator: TextGenerator | None = None,
) -> Explanation:
    """Generate a cautious explanation, or abstain when evidence is insufficient."""
    if not evidence:
        return Explanation(
            summary="No temporally eligible evidence was found for this movement.",
            confidence="low",
            citations=(),
            limitations=("The system cannot attribute the movement without evidence.",),
            abstained=True,
        )
    payload = _evidence_payload(evidence)
    if generator is None:
        first = payload[0]
        return Explanation(
            summary=(
                f"The movement coincided with reporting from {first['source']} about "
                f"{first['title']} [E1]. This is temporal association, not proof of cause."
            ),
            confidence="medium" if len(evidence) > 1 else "low",
            citations=("E1",),
            limitations=("Public news may omit relevant non-public or macro information.",),
            abstained=False,
        )

    prompt = (
        "Event:\n" + json.dumps(event, default=str) + "\nEvidence:\n" +
        json.dumps(payload) +
        "\nReturn JSON with summary, confidence (low/medium/high), citations, limitations. "
        "Explain the strongest supported company, sector, or market association in plain "
        "language. Every factual news claim must cite [E#]. Never state causation as fact, "
        "and explicitly acknowledge weak or conflicting evidence."
    )
    raw = generator.generate(
        system="You are a cautious financial research assistant grounded only in supplied evidence.",
        prompt=prompt,
    )
    try:
        parsed = json.loads(raw)
        summary = str(parsed["summary"])
        citations = tuple(CITATION_PATTERN.findall(summary))
        allowed = {item["citation"] for item in payload}
        if not citations or not set(citations) <= allowed:
            raise ValueError("Missing or invalid citations")
        confidence = str(parsed.get("confidence", "low")).lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "low"
        return Explanation(
            summary=summary,
            confidence=confidence,
            citations=citations,
            limitations=tuple(map(str, parsed.get("limitations", ()))),
            abstained=False,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return Explanation(
            summary="The generated explanation failed grounding validation.",
            confidence="low",
            citations=(),
            limitations=("Model output was malformed or contained unsupported citations.",),
            abstained=True,
        )
