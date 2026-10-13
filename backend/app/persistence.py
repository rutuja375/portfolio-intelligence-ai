import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class InvestigationStore:
    def __init__(self, path: str | Path = "data/investigations.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT
                )"""
            )

    def create(self, request: dict) -> str:
        identifier = str(uuid4())
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO investigations VALUES (?, ?, ?, ?, NULL, NULL)",
                (identifier, datetime.now(UTC).isoformat(), "queued", json.dumps(request)),
            )
        return identifier

    def update(
        self, identifier: str, *, status: str, result: dict | None = None, error: str | None = None
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE investigations SET status=?, result_json=?, error=? WHERE id=?",
                (status, json.dumps(result, default=str) if result else None, error, identifier),
            )

    def get(self, identifier: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, created_at, status, request_json, result_json, error "
                "FROM investigations WHERE id=?",
                (identifier,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "created_at": row[1],
            "status": row[2],
            "request": json.loads(row[3]),
            "result": json.loads(row[4]) if row[4] else None,
            "error": row[5],
        }
