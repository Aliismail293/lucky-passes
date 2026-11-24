"""A disk cache for model calls, so a crashed or stopped run picks up where it left off.

Each call is stored under a SHA-256 hash of everything that can change its output:
the kind of call, the model, the prompt (which already contains any retrieved context) and the parameters.
SQLite is used because each write is committed straight away, so a crash loses at most the call in flight.
"""

import hashlib
import json
import sqlite3
from pathlib import Path


def make_key(kind: str, model: str, payload: dict) -> str:
    blob = json.dumps({"kind": kind, "model": model, "payload": payload}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class Cache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS calls (key TEXT PRIMARY KEY, model TEXT, value TEXT)")
        self._db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, value BLOB)")
        self._db.commit()

    def get(self, key: str) -> str | None:
        row = self._db.execute("SELECT value FROM calls WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, model: str, value: str) -> None:
        self._db.execute("INSERT OR REPLACE INTO calls VALUES (?, ?, ?)", (key, model, value))
        self._db.commit()

    def get_vector(self, key: str) -> bytes | None:
        row = self._db.execute("SELECT value FROM vectors WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def put_vectors(self, items: list[tuple[str, bytes]]) -> None:
        self._db.executemany("INSERT OR REPLACE INTO vectors VALUES (?, ?)", items)
        self._db.commit()

    def count(self, model: str | None = None) -> int:
        if model is None:
            return self._db.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
        return self._db.execute("SELECT COUNT(*) FROM calls WHERE model = ?", (model,)).fetchone()[0]

    def close(self) -> None:
        self._db.close()
