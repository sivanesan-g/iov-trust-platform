import sqlite3
from pathlib import Path

from backend.config import BASE_DIR


class ReplayGuard:
    def __init__(self, db_path=None):
        base_dir = BASE_DIR / "data"
        base_dir.mkdir(parents=True, exist_ok=True)
        effective_path = str(db_path) if db_path is not None else str(base_dir / "processed_messages.db")
        self._in_memory = effective_path == ":memory:"
        self.db_path = effective_path if self._in_memory else Path(effective_path)
        if not self._in_memory:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            ":memory:" if self._in_memory else str(self.db_path),
            check_same_thread=False,
        )
        self._initialize()

    def _initialize(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_messages (
                vehicle_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                PRIMARY KEY (vehicle_id, message_id, sequence)
            )
            """
        )
        self._conn.commit()

    def is_duplicate(self, vehicle_id: str, message_id: str, sequence: int):
        row = self._conn.execute(
            "SELECT 1 FROM processed_messages WHERE vehicle_id=? AND message_id=? AND sequence=?",
            (str(vehicle_id), str(message_id), int(sequence)),
        ).fetchone()
        return row is not None

    def mark_processed(self, vehicle_id: str, message_id: str, sequence: int):
        self._conn.execute(
            "INSERT OR IGNORE INTO processed_messages (vehicle_id, message_id, sequence) VALUES (?, ?, ?)",
            (str(vehicle_id), str(message_id), int(sequence)),
        )
        self._conn.commit()

    def clear_if_needed(self):
        self._conn.execute("DELETE FROM processed_messages WHERE rowid IN (SELECT rowid FROM processed_messages LIMIT 5000)")
        self._conn.commit()
