# Portfolio Intelligence AI

An investigation-oriented MVP for answering: **what moved a historical portfolio,
what was unusual, and what public evidence was available at that time?** It is a
research aid, not investment advice and not a causal inference engine.

## What is implemented

- Alpaca IEX minute-bar retrieval with exchange-calendar filtering and OHLCV validation.
- Timestamp alignment that preserves missing values; prices are never forward-filled or invented.
- Contributions, synchronized portfolio returns, compounding, and data-quality diagnostics.
- Leakage-free rolling median/MAD anomalies plus market beta and sector-relative context.
- Time-gated Alpaca news retrieval and transparent symbol/keyword/recency ranking.
- Grounded explanations with `[E#]` citations, uncertainty, validation, and abstention.
- Optional FinBERT, OpenAI Responses API generation, and LangGraph orchestration.
- FastAPI, dashboard, SQLite persistence, background jobs, tests, Docker, CI, and Render config.

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

Open <http://localhost:8000> for the dashboard or <http://localhost:8000/docs>
for the API. `POST /v1/investigations` accepts validated historical return
observations and timestamped evidence; poll the returned ID at
`GET /v1/investigations/{id}`.

Run `python scripts/demo.py` for an offline control-flow demo. Its values and article
are illustrative fixtures, not market observations or evidence about a real security.
Use Alpaca-backed inputs for real investigations.

## Credentials and optional services

Never commit `.env` or API keys.

- `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`: required for live Alpaca IEX bars and news.
- `OPENAI_API_KEY`: optional; otherwise use the conservative deterministic explanation.
- Install `.[ai]` for OpenAI, FinBERT, and LangGraph. FinBERT downloads weights on first use.
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
- Fixed weights do not model trades, cash flows, fees, slippage, taxes, or corporate actions.
- Provider news timestamps and tags can be imperfect; timing does not prove reaction or cause.
- Statistical anomalies identify unusual observations, not causes.
- Evidence ranking is deliberately simple; FinBERT sentiment is context, not causal evidence.
- Public news can miss macro events, filings, analyst notes, rumors, and private information.
- In-process background tasks can be interrupted by restarts; production needs a durable queue.

## Evaluation

Tests cover return math, market sessions, missing data, cumulative performance, quality,
anomaly leakage, beta context, future-news exclusion, citations, abstention, persistence,
and API job round-trips. Evaluation reports citation validity, temporal eligibility, and
abstention correctness. Before decision-making use, add a human-labeled event set and
measure retrieval recall, false anomaly rate, calibration, and expert-rated faithfulness.
