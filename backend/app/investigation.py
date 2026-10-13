from dataclasses import asdict
from datetime import datetime

from app.analytics.anomalies import contextualize_return, detect_rolling_anomalies
from app.evaluation import evaluate_explanation
from app.evidence.models import Article
from app.evidence.retrieval import rank_evidence
from app.explanations.grounding import TextGenerator, explain_with_evidence


def investigate_movement(
    *,
    symbol: str,
    observations: list[tuple[datetime, float]],
    articles: list[Article],
    market_returns: list[float] | None = None,
    sector_return: float | None = None,
    generator: TextGenerator | None = None,
    window: int = 30,
    threshold: float = 3.5,
) -> dict:
    """Run the deterministic investigation pipeline over already validated inputs."""
    anomalies = detect_rolling_anomalies(
        observations, window=window, threshold=threshold
    )
    if not anomalies:
        return {"symbol": symbol, "status": "no_anomaly", "events": []}
    event = anomalies[-1]
    asset_history = [value for _, value in observations[:-1]]
    context = contextualize_return(
        event.value,
        market_returns[-1] if market_returns else 0.0,
        sector_return=sector_return,
        asset_history=asset_history[-window:] if market_returns else None,
        market_history=market_returns[-window - 1:-1] if market_returns else None,
    )
    evidence = rank_evidence(
        articles,
        symbols=[symbol],
        event_time=event.timestamp,
        query=f"{symbol} shares outlook earnings guidance",
    )
    explanation = explain_with_evidence(asdict(event), evidence, generator)
    evaluation = evaluate_explanation(explanation, evidence, event.timestamp)
    return {
        "symbol": symbol,
        "status": "completed",
        "events": [
            {
                "anomaly": asdict(event),
                "context": asdict(context),
                "evidence": [
                    {
                        "citation": f"E{index}",
                        "title": item.article.title,
                        "url": item.article.url,
                        "source": item.article.source,
                        "published_at": item.article.published_at,
                        "score": item.score,
                        "reasons": item.reasons,
                    }
                    for index, item in enumerate(evidence, start=1)
                ],
                "explanation": asdict(explanation),
                "evaluation": asdict(evaluation),
            }
        ],
    }
