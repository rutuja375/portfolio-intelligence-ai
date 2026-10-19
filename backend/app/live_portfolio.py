import os
from datetime import datetime

from alpaca.data.historical import NewsClient, StockHistoricalDataClient

from app.evidence.ai_ranking import local_evidence_ai
from app.evidence.alpaca_news import AlpacaNewsProvider
from app.explanations.grounding import OllamaGenerator, OpenAIResponsesGenerator
from app.market_data.alpaca_provider import fetch_regular_session_bars
from app.portfolio_investigation import investigate_portfolio_history


def run_live_portfolio_investigation(
    *,
    weights: dict[str, float],
    start: datetime,
    end: datetime,
    window: int = 30,
    threshold: float = 3.5,
    horizons: tuple[int, ...] = (1, 5, 15),
    confirmation_horizon: int = 5,
    volatility_threshold: float = 2.0,
    volume_threshold: float = 1.5,
) -> dict:
    """Retrieve Alpaca IEX bars/news and run a historical portfolio investigation."""
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca API credentials in .env")
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Start and end must include timezone information")
    if start >= end:
        raise ValueError("Start must be before end")

    symbols = list(weights)
    market_client = StockHistoricalDataClient(api_key, secret_key)
    requested_symbols = list(dict.fromkeys([*symbols, "SPY", "QQQ"]))
    all_bars = fetch_regular_session_bars(
        market_client, requested_symbols, start, end
    )
    bars_by_symbol = {symbol: all_bars[symbol] for symbol in symbols}
    news = list(
        AlpacaNewsProvider(NewsClient(api_key, secret_key)).search(
            requested_symbols, start, end
        )
    )
    ai_enabled = os.getenv("AI_EVIDENCE_ENABLED", "false").lower() in {
        "1", "true", "yes", "on"
    }
    evidence_ai = local_evidence_ai() if ai_enabled else None
    generator = _build_generator() if ai_enabled else None
    return investigate_portfolio_history(
        weights=weights,
        bars_by_symbol=bars_by_symbol,
        articles=news,
        benchmark_bars=all_bars["SPY"],
        sector_bars=all_bars["QQQ"],
        window=window,
        threshold=threshold,
        horizons=horizons,
        confirmation_horizon=confirmation_horizon,
        volatility_threshold=volatility_threshold,
        volume_threshold=volume_threshold,
        evidence_ai=evidence_ai,
        generator=generator,
    )


def _build_generator():
    provider = os.getenv("LLM_PROVIDER", "deterministic").strip().lower()
    if provider == "ollama":
        return OllamaGenerator(
            model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        )
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("LLM_PROVIDER=openai requires OPENAI_API_KEY")
        return OpenAIResponsesGenerator(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini")
        )
    if provider not in {"deterministic", "none"}:
        raise ValueError("LLM_PROVIDER must be deterministic, ollama, or openai")
    return None
