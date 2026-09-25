from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rule_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    rules_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quality_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    rule_set_id INTEGER NOT NULL,
    score REAL NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    total_violations INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(dataset_id) REFERENCES datasets(id),
    FOREIGN KEY(rule_set_id) REFERENCES rule_sets(id)
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_dataset(self, name: str, filename: str, file_path: str, profile: dict[str, Any]) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO datasets(name,filename,file_path,row_count,column_count,profile_json,created_at) VALUES(?,?,?,?,?,?,?)",
                (name, filename, file_path, profile["row_count"], profile["column_count"], json.dumps(profile), utc_now()),
            )
            return int(cur.lastrowid)

    def list_datasets(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM datasets ORDER BY id DESC").fetchall()
        return [self._dataset(row) for row in rows]

    def get_dataset(self, dataset_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM datasets WHERE id=?", (dataset_id,)).fetchone()
        return self._dataset(row) if row else None

    def create_rule_set(self, name: str, rules: list[dict[str, Any]]) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO rule_sets(name,rules_json,created_at) VALUES(?,?,?)",
                (name, json.dumps(rules), utc_now()),
            )
            return int(cur.lastrowid)

    def list_rule_sets(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM rule_sets ORDER BY id DESC").fetchall()
        return [self._rule_set(row) for row in rows]

    def get_rule_set(self, rule_set_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM rule_sets WHERE id=?", (rule_set_id,)).fetchone()
        return self._rule_set(row) if row else None

    def create_run(self, dataset_id: int, rule_set_id: int, result: dict[str, Any]) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO quality_runs(dataset_id,rule_set_id,score,passed,failed,total_violations,result_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (dataset_id, rule_set_id, result["score"], result["passed"], result["failed"], result["total_violations"], json.dumps(result), utc_now()),
            )
            return int(cur.lastrowid)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT q.*, d.name dataset_name, r.name rule_set_name
                   FROM quality_runs q JOIN datasets d ON d.id=q.dataset_id JOIN rule_sets r ON r.id=q.rule_set_id
                   ORDER BY q.id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [self._run(row) for row in rows]

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """SELECT q.*, d.name dataset_name, r.name rule_set_name
                   FROM quality_runs q JOIN datasets d ON d.id=q.dataset_id JOIN rule_sets r ON r.id=q.rule_set_id
                   WHERE q.id=?""",
                (run_id,),
            ).fetchone()
        return self._run(row) if row else None

    @staticmethod
    def _dataset(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["profile"] = json.loads(item.pop("profile_json"))
        return item

    @staticmethod
    def _rule_set(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["rules"] = json.loads(item.pop("rules_json"))
        return item

    @staticmethod
    def _run(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json"))
        return item
