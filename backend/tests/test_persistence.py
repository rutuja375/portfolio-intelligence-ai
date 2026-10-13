from app.persistence import InvestigationStore


def test_store_round_trip(tmp_path):
    store = InvestigationStore(tmp_path / "test.db")
    identifier = store.create({"symbol": "AAPL"})
    store.update(identifier, status="completed", result={"events": []})
    record = store.get(identifier)
    assert record["status"] == "completed"
    assert record["result"] == {"events": []}
