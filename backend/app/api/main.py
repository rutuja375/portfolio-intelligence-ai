import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl

from app.evidence.models import Article
from app.investigation import investigate_movement
from app.live_portfolio import run_live_portfolio_investigation
from app.persistence import InvestigationStore

load_dotenv()
app = FastAPI(title="Portfolio Intelligence AI", version="0.2.0")
store = InvestigationStore(os.getenv("DATABASE_PATH", "data/investigations.db"))


class ReturnPoint(BaseModel):
    timestamp: datetime
    value: float = Field(gt=-1)


class ArticleInput(BaseModel):
    id: str
    title: str
    url: HttpUrl
    source: str
    published_at: datetime
    summary: str = ""
    symbols: list[str] = []


class InvestigationInput(BaseModel):
    symbol: str = Field(pattern=r"^[A-Za-z.]{1,10}$")
    observations: list[ReturnPoint] = Field(min_length=4)
    articles: list[ArticleInput] = []
    market_returns: list[float] | None = None
    sector_return: float | None = None
    window: int = Field(default=30, ge=3, le=390)
    threshold: float = Field(default=3.5, gt=0)


class HoldingInput(BaseModel):
    symbol: str = Field(pattern=r"^[A-Za-z.]{1,10}$")
    weight: float = Field(gt=0, le=1)


class PortfolioInvestigationInput(BaseModel):
    holdings: list[HoldingInput] = Field(min_length=1, max_length=20)
    start: datetime
    end: datetime
    window: int = Field(default=30, ge=3, le=390)
    threshold: float = Field(default=3.5, gt=0)


def _run(identifier: str, request: dict) -> None:
    try:
        request["observations"] = [
            (item["timestamp"], item["value"]) for item in request["observations"]
        ]
        request["articles"] = [
            Article(**{**item, "url": str(item["url"])}) for item in request["articles"]
        ]
        store.update(identifier, status="running")
        result = investigate_movement(**request)
        store.update(identifier, status="completed", result=result)
    except Exception as error:  # noqa: BLE001 - job failures must be persisted
        store.update(identifier, status="failed", error=str(error))


def _run_portfolio(identifier: str, request: dict) -> None:
    try:
        weights = {
            item["symbol"].upper(): item["weight"] for item in request.pop("holdings")
        }
        if abs(sum(weights.values()) - 1.0) > 1e-9:
            raise ValueError("Portfolio weights must sum to 100%")
        store.update(identifier, status="running")
        result = run_live_portfolio_investigation(weights=weights, **request)
        store.update(identifier, status="completed", result=result)
    except Exception as error:  # noqa: BLE001 - job failures must be persisted
        store.update(identifier, status="failed", error=str(error))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/investigations", status_code=202)
def create_investigation(payload: InvestigationInput, tasks: BackgroundTasks) -> dict:
    request = payload.model_dump(mode="json")
    identifier = store.create(request)
    tasks.add_task(_run, identifier, payload.model_dump())
    return {"id": identifier, "status": "queued"}


@app.post("/v1/portfolio-investigations", status_code=202)
def create_portfolio_investigation(
    payload: PortfolioInvestigationInput, tasks: BackgroundTasks
) -> dict:
    request = payload.model_dump(mode="json")
    identifier = store.create(request)
    tasks.add_task(_run_portfolio, identifier, payload.model_dump())
    return {"id": identifier, "status": "queued"}


@app.get("/v1/investigations/{identifier}")
def get_investigation(identifier: str) -> dict:
    investigation = store.get(identifier)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parents[1] / "static" / "index.html")
