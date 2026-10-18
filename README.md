# Portfolio Intelligence AI

An investigation-oriented MVP for answering: **what moved a portfolio, what was
unusual, and what public evidence was available at that time?** It is a
research aid, not investment advice and not a causal inference engine.

## What is implemented

- Alpaca IEX minute-bar retrieval with exchange-calendar filtering and OHLCV validation.
- Timestamp alignment that preserves missing values; prices are never forward-filled or invented.
- Contributions, synchronized portfolio returns, compounding, and data-quality diagnostics.
- Leakage-free 1/5/15-minute signals with rolling MAD, volatility adjustment,
  abnormal-volume confirmation, and nearby-signal event grouping.
- Company-news, broader-market-context, and evidence-free abstention branches.
- Time-gated Alpaca news retrieval with optional semantic embeddings, cross-encoder
  reranking, FinBERT sentiment, financial-event tags, and transparent hybrid scores.
- Grounded explanations with `[E#]` citations, uncertainty, validation, and abstention.
- Optional FinBERT, OpenAI Responses API generation, and LangGraph orchestration.
- FastAPI, auto-refreshing saved-portfolio dashboard, SQLite persistence, background
  jobs, tests, Docker, CI, and Render config.

## Architecture

```text
Alpaca IEX bars -> validation -> alignment -> returns/attribution -> anomaly/context
                                                                      |
Alpaca news ----> event-time cutoff -> evidence ranking --------------+
                                                                      v
                                               grounded explanation + evaluation
                                                                      v
                                                    FastAPI / SQLite / dashboard
```

The statistical core and deterministic fallback do not need an LLM. LangGraph is
optional because the current graph has one bounded investigation node; it becomes useful
when durable retries, human review, or multiple retrieval/model branches are added.

## Local setup

Requires Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m pytest -q
python -m ruff check backend
uvicorn app.api.main:app --reload
```

Open <http://localhost:8000> for the interactive dashboard or
<http://localhost:8000/docs> for the API. The dashboard accepts portfolio symbols,
weights and anomaly sensitivity, then evaluates the most recent three-day rolling
window once per minute. The browser saves the portfolio locally and automatically
resumes monitoring on a return visit. It renders performance, data quality,
contributors, market context, evidence, and the grounded explanation. The lower-level
`POST /v1/investigations` endpoint remains available for supplied return observations;
poll either workflow at `GET /v1/investigations/{id}`.

Run `python scripts/demo.py` for an offline control-flow demo. Its values and article
are illustrative fixtures, not market observations or evidence about a real security.
Use Alpaca-backed inputs for real investigations.

## Credentials and optional services

Never commit `.env` or API keys.

- `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`: required for live Alpaca IEX bars and news.
- `OPENAI_API_KEY`: optional; otherwise use the conservative deterministic explanation.
- `AI_EVIDENCE_ENABLED=true`: enables local embeddings, cross-encoder reranking, and
  FinBERT. The first run downloads model weights and can take several minutes.
- `OPENAI_MODEL`: model used for the optional grounded explanation (default `gpt-5-mini`).
- Install `.[ai]` for embeddings, cross-encoder reranking, FinBERT, OpenAI, and
  LangGraph. Local model weights download on first use.
- SQLite is sufficient for one-process MVP use. Multi-worker deployment needs PostgreSQL and a durable queue.

## Docker and deployment

```powershell
docker compose up --build
```

`render.yaml` is configuration only. Deployment is not complete until the service is
provisioned, secrets supplied, persistent disk attached, and `/health` verified. GitHub
Actions runs lint, tests, and a container build; it does not publish or deploy images.

## Reliability boundaries

- IEX is a limited US-equity feed and can differ from consolidated SIP data.
- Current monitoring uses one-minute REST snapshots, not a continuously open Alpaca
  WebSocket. A browser must remain open for automatic refresh; server-side always-on
  monitoring and alerts remain a later milestone.
- Fixed weights do not model trades, cash flows, fees, slippage, taxes, or corporate actions.
- Provider news timestamps and tags can be imperfect; timing does not prove reaction or cause.
- Statistical anomalies identify unusual observations, not causes.
- Publication-time filtering remains deterministic and happens before all AI ranking.
- Embedding, reranker, and FinBERT scores improve retrieval but do not prove causation.
- With AI disabled or without an OpenAI key, the safe deterministic ranking and explanation
  remain available. Model-loading failures are surfaced instead of silently changing modes.
- Public news can miss macro events, filings, analyst notes, rumors, and private information.
- In-process background tasks can be interrupted by restarts; production needs a durable queue.

## Evaluation

Tests cover return math, market sessions, missing data, cumulative performance, quality,
anomaly leakage, beta context, future-news exclusion, citations, abstention, persistence,
and API job round-trips. Evaluation reports citation validity, temporal eligibility, and
abstention correctness. Before decision-making use, add a human-labeled event set and
measure retrieval recall, false anomaly rate, calibration, and expert-rated faithfulness.
