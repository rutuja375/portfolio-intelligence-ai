from dataclasses import asdict
from datetime import datetime
from itertools import pairwise

from app.analytics.anomalies import contextualize_return, detect_rolling_anomalies
from app.analytics.performance import cumulative_performance
from app.analytics.timeseries import calculate_synchronized_portfolio_returns
from app.evaluation import evaluate_explanation
from app.evidence.retrieval import rank_evidence
from app.explanations.grounding import explain_with_evidence
from app.market_data.alignment import align_bars_by_timestamp
from app.market_data.quality import assess_data_quality


def investigate_portfolio_history(
    *,
    weights: dict[str, float],
    bars_by_symbol: dict[str, list],
    articles: list,
    benchmark_bars: list | None = None,
    sector_bars: list | None = None,
    window: int = 30,
    threshold: float = 3.5,
) -> dict:
    """Investigate synchronized portfolio history without filling missing prices."""
    aligned = align_bars_by_timestamp(bars_by_symbol)
    quality = assess_data_quality(bars_by_symbol, aligned)
    portfolio_returns = calculate_synchronized_portfolio_returns(aligned, weights)
    performance = cumulative_performance(portfolio_returns)
    observations = [
        (item["timestamp"], item["portfolio_return"]) for item in portfolio_returns
    ]
    anomalies = detect_rolling_anomalies(
        observations, window=window, threshold=threshold
    )
    response = {
        "status": "completed",
        "portfolio": {"weights": weights, "symbols": list(weights)},
        "summary": {
            "observations": len(portfolio_returns),
            "anomalies": len(anomalies),
            "cumulative_return": (
                performance[-1].cumulative_return if performance else 0.0
            ),
            "coverage": quality.coverage,
        },
        "quality": quality.to_dict(),
        "performance": [asdict(point) for point in performance],
        "events": [],
    }
    if not anomalies:
        response["status"] = "no_anomaly"
        return response

    event = anomalies[-1]
    event_return = next(
        item for item in portfolio_returns if item["timestamp"] == event.timestamp
    )
    contributions = event_return["contributions"]
    primary_symbol = max(contributions, key=lambda symbol: abs(contributions[symbol]))
    benchmark_returns = _returns_by_timestamp(benchmark_bars or [])
    sector_returns = _returns_by_timestamp(sector_bars or [])
    market_return = benchmark_returns.get(event.timestamp, 0.0)
    sector_return = sector_returns.get(event.timestamp)
    context = contextualize_return(
        event.value,
        market_return,
        sector_return=sector_return,
    )
    evidence = rank_evidence(
        articles,
        symbols=list(weights),
        event_time=event.timestamp,
        query=" ".join(weights) + " earnings guidance outlook shares",
    )
    event_payload = {
        **asdict(event),
        "primary_symbol": primary_symbol,
        "contributions": contributions,
    }
    explanation = explain_with_evidence(event_payload, evidence)
    evaluation = evaluate_explanation(explanation, evidence, event.timestamp)
    response["events"] = [
        {
            "anomaly": asdict(event),
            "primary_symbol": primary_symbol,
            "stock_returns": event_return["stock_returns"],
            "contributions": contributions,
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
    ]
    return response


def _returns_by_timestamp(bars: list) -> dict[datetime, float]:
    result = {}
    for previous, current in pairwise(bars):
        if previous.close > 0:
            result[current.timestamp] = current.close / previous.close - 1
    return result
