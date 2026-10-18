from dataclasses import asdict
from datetime import datetime, timedelta

from app.analytics.anomalies import contextualize_return
from app.analytics.event_signals import (
    calculate_multi_window_signals,
    group_confirmed_events,
)
from app.analytics.performance import cumulative_performance
from app.analytics.timeseries import calculate_synchronized_portfolio_returns
from app.evaluation import evaluate_explanation
from app.evidence.ai_ranking import EvidenceAI
from app.evidence.retrieval import rank_evidence
from app.explanations.grounding import Explanation, TextGenerator, explain_with_evidence
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
    horizons: tuple[int, ...] = (1, 5, 15),
    confirmation_horizon: int = 5,
    volatility_threshold: float = 2.0,
    volume_threshold: float = 1.5,
    evidence_ai: EvidenceAI | None = None,
    generator: TextGenerator | None = None,
) -> dict:
    """Investigate synchronized portfolio history without filling missing prices."""
    aligned = align_bars_by_timestamp(bars_by_symbol)
    quality = assess_data_quality(bars_by_symbol, aligned)
    portfolio_returns = calculate_synchronized_portfolio_returns(aligned, weights)
    performance = cumulative_performance(portfolio_returns)
    signals = calculate_multi_window_signals(
        bars_by_symbol,
        weights,
        horizons=horizons,
        baseline_window=window,
        threshold=threshold,
        volatility_threshold=volatility_threshold,
        volume_threshold=volume_threshold,
        confirmation_horizon=confirmation_horizon,
    )
    grouped_events = group_confirmed_events(signals)
    response = {
        "status": "completed",
        "portfolio": {"weights": weights, "symbols": list(weights)},
        "summary": {
            "observations": len(portfolio_returns),
            "anomalies": len(grouped_events),
            "candidate_signals": len(signals),
            "cumulative_return": (
                performance[-1].cumulative_return if performance else 0.0
            ),
            "coverage": quality.coverage,
        },
        "quality": quality.to_dict(),
        "performance": [asdict(point) for point in performance],
        "events": [],
    }
    if not grouped_events:
        response["status"] = "no_anomaly"
        return response

    article_list = list(articles)
    company_symbols = set(weights)
    company_articles = [
        article
        for article in article_list
        if company_symbols & {symbol.upper() for symbol in article.symbols}
    ]
    market_articles = [
        article
        for article in article_list
        if {"SPY", "QQQ"} & {symbol.upper() for symbol in article.symbols}
    ]
    benchmark_returns = _returns_by_timestamp(
        benchmark_bars or [], horizon=confirmation_horizon
    )
    sector_returns = _returns_by_timestamp(
        sector_bars or [], horizon=confirmation_horizon
    )
    for grouped in grouped_events:
        signal = grouped["peak"]
        contributions = signal.contributions
        primary_symbol = max(contributions, key=lambda symbol: abs(contributions[symbol]))
        market_return = benchmark_returns.get(signal.timestamp, 0.0)
        sector_return = sector_returns.get(signal.timestamp)
        context = contextualize_return(
            signal.portfolio_return,
            market_return,
            sector_return=sector_return,
        )
        evidence = rank_evidence(
            company_articles,
            symbols=list(weights),
            event_time=signal.timestamp,
            query=" ".join(weights) + " earnings guidance outlook shares",
            ai=evidence_ai,
            movement_direction=1 if signal.portfolio_return > 0 else -1,
        )
        market_same_direction = market_return * signal.portfolio_return > 0
        sector_same_direction = (
            sector_return is not None and sector_return * signal.portfolio_return > 0
        )
        market_wide = (
            max(abs(market_return), abs(sector_return or 0.0))
            >= max(0.001, abs(signal.portfolio_return) * 0.5)
            and (market_same_direction or sector_same_direction)
        )
        evidence_scope = "company"
        if not evidence and market_wide:
            evidence_scope = "market"
            evidence = rank_evidence(
                market_articles,
                symbols=("SPY", "QQQ"),
                event_time=signal.timestamp,
                query="market economy rates inflation technology shares",
                ai=evidence_ai,
                movement_direction=1 if signal.portfolio_return > 0 else -1,
            )
        event_payload = {
            **signal.to_dict(),
            "primary_symbol": primary_symbol,
            "event_start": grouped["start"],
            "event_end": grouped["end"],
        }
        if evidence:
            explanation = explain_with_evidence(event_payload, evidence, generator)
        elif market_wide:
            direction = "increase" if signal.portfolio_return > 0 else "decline"
            explanation = Explanation(
                summary=(
                    "No sufficiently relevant company-specific evidence was found. "
                    f"The movement occurred alongside a broader {direction} in SPY or "
                    "QQQ, suggesting that market-wide conditions may have contributed."
                ),
                confidence="low",
                citations=(),
                limitations=(
                    "Synchronized movement is contextual evidence, not proof of cause.",
                ),
                abstained=False,
            )
        else:
            explanation = Explanation(
                summary=(
                    "A significant portfolio movement was detected, but no sufficiently "
                    "relevant company or broader-market evidence was found. The system "
                    "abstained from providing an explanation."
                ),
                confidence="low",
                citations=(),
                limitations=("The system cannot attribute the movement without evidence.",),
                abstained=True,
            )
        evaluation = evaluate_explanation(
            explanation,
            evidence,
            signal.timestamp,
            context_supported=market_wide,
        )
        response["events"].append({
            "anomaly": {
                "timestamp": signal.timestamp,
                "value": signal.portfolio_return,
                "score": signal.mad_score,
                "direction": "up" if signal.portfolio_return > 0 else "down",
                "method": "multi_window_mad",
            },
            "event_window": {
                "start": grouped["start"],
                "end": grouped["end"],
                "horizon_minutes": signal.horizon_minutes,
            },
            "confirmation": {
                "volatility_score": signal.volatility_score,
                "volume_ratio": signal.volume_ratio,
                "confirmed": signal.confirmed,
            },
            "primary_symbol": primary_symbol,
            "stock_returns": signal.stock_returns,
            "contributions": contributions,
            "context": asdict(context),
            "evidence_scope": evidence_scope,
            "evidence": [
                {
                    "citation": f"E{index}",
                    "title": item.article.title,
                    "url": item.article.url,
                    "source": item.article.source,
                    "published_at": item.article.published_at,
                    "score": item.score,
                    "reasons": item.reasons,
                    "semantic_score": item.semantic_score,
                    "reranker_score": item.reranker_score,
                    "sentiment": item.sentiment,
                    "event_tags": item.event_tags,
                }
                for index, item in enumerate(evidence, start=1)
            ],
            "explanation": asdict(explanation),
            "evaluation": asdict(evaluation),
            "ranking_mode": "hybrid_ai" if evidence_ai is not None else "deterministic",
        })
    return response


def _returns_by_timestamp(bars: list, *, horizon: int = 1) -> dict[datetime, float]:
    result = {}
    by_time = {bar.timestamp: bar for bar in bars}
    for current in bars:
        previous = by_time.get(current.timestamp - timedelta(minutes=horizon))
        if previous is not None and previous.close > 0:
            result[current.timestamp] = current.close / previous.close - 1
    return result
