import json
import os
import sqlite3
from datetime import datetime, UTC
from pathlib import Path


class CloudStore:
    def __init__(self, db_path=None, db_name="trust_events.db"):
        base_dir = Path(__file__).resolve().parents[1]
        self.db_path = Path(db_path or os.getenv("LOCAL_DB_PATH", base_dir / "data" / db_name))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trust_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, record: dict):
        try:
            data = dict(record)
            data["saved_at"] = datetime.now(UTC).isoformat()
            payload = json.dumps(data, default=str)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO trust_events (vehicle_id, payload, saved_at) VALUES (?, ?, ?)",
                    (str(data.get("vehicle_id", "")), payload, data["saved_at"]),
                )
                conn.commit()

            return True, {
                "status": "saved_database",
                "inserted_id": str(cursor.lastrowid),
            }

        except Exception as exc:
            return False, {
                "status": "db_error",
                "reason": str(exc),
            }

    def list_entries(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, vehicle_id, payload, saved_at FROM trust_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            {
                "id": row[0],
                "vehicle_id": row[1],
                "payload": json.loads(row[2]),
                "saved_at": row[3],
            }
            for row in rows
        ]