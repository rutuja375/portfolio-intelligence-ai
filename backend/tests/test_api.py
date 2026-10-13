from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def test_health_endpoint(tmp_path, monkeypatch):
    from app.api import main
    from app.persistence import InvestigationStore

    monkeypatch.setattr(main, "store", InvestigationStore(tmp_path / "api.db"))
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_background_investigation_round_trip(tmp_path, monkeypatch):
    from app.api import main
    from app.persistence import InvestigationStore

    monkeypatch.setattr(main, "store", InvestigationStore(tmp_path / "api.db"))
    client = TestClient(main.app)
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    response = client.post(
        "/v1/investigations",
        json={
            "symbol": "AAPL",
            "observations": [
                {"timestamp": (start + timedelta(minutes=index)).isoformat(), "value": value}
                for index, value in enumerate([0, .001, -.001, .002, -.002, .001, .05])
            ],
            "articles": [],
            "window": 6,
        },
    )
    assert response.status_code == 202
    record = client.get(f"/v1/investigations/{response.json()['id']}").json()
    assert record["status"] == "completed"
    assert record["result"]["events"][0]["explanation"]["abstained"] is True


def test_portfolio_dashboard_job_round_trip(tmp_path, monkeypatch):
    from app.api import main
    from app.persistence import InvestigationStore

    monkeypatch.setattr(main, "store", InvestigationStore(tmp_path / "portfolio.db"))
    monkeypatch.setattr(
        main,
        "run_live_portfolio_investigation",
        lambda **kwargs: {
            "status": "no_anomaly",
            "summary": {"observations": 10, "anomalies": 0},
            "events": [],
        },
    )
    client = TestClient(main.app)
    response = client.post(
        "/v1/portfolio-investigations",
        json={
            "holdings": [
                {"symbol": "AAPL", "weight": 0.6},
                {"symbol": "MSFT", "weight": 0.4},
            ],
            "start": "2026-01-02T00:00:00Z",
            "end": "2026-01-03T00:00:00Z",
            "window": 30,
            "threshold": 3.5,
        },
    )
    assert response.status_code == 202
    record = client.get(f"/v1/investigations/{response.json()['id']}").json()
    assert record["status"] == "completed"
    assert record["result"]["status"] == "no_anomaly"
