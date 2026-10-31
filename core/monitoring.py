from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from core.config import settings


@dataclass
class Event:
    event_type: str
    agent: str = "system"
    latency_ms: float = 0.0
    success: bool = True
    failure_mode: str | None = None
    user_id: str = "anonymous"
    query_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] | None = None


class Monitor:
    """轻量 SQLite 事件仓库；线程安全，页面与 Agent 可共享。"""

    def __init__(self, path: Path | str = settings.monitor_db):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL, agent TEXT NOT NULL,
                    latency_ms REAL NOT NULL, success INTEGER NOT NULL,
                    failure_mode TEXT, user_id TEXT, query_id TEXT,
                    prompt_tokens INTEGER, completion_tokens INTEGER,
                    cost_usd REAL, metadata TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                    query_id TEXT NOT NULL, user_id TEXT, value INTEGER NOT NULL,
                    comment TEXT
                );
                CREATE TABLE IF NOT EXISTS index_state (
                    collection TEXT PRIMARY KEY, chunks INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL, model TEXT NOT NULL
                );
                """
            )

    def record(self, event: Event) -> None:
        row = asdict(event)
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(),
                    row["event_type"], row["agent"], row["latency_ms"],
                    int(row["success"]), row["failure_mode"], row["user_id"],
                    row["query_id"], row["prompt_tokens"], row["completion_tokens"],
                    row["cost_usd"], json.dumps(row["metadata"] or {}, ensure_ascii=False),
                ),
            )

    @contextmanager
    def timed(self, event_type: str, agent: str, **fields: Any) -> Iterator[dict[str, Any]]:
        start = time.perf_counter()
        outcome: dict[str, Any] = {"success": True, "failure_mode": None, "metadata": {}}
        try:
            yield outcome
        except TimeoutError:
            outcome.update(success=False, failure_mode="timeout")
            raise
        except Exception as exc:
            outcome.update(success=False, failure_mode=self.classify_failure(exc))
            outcome["metadata"] = {"error": str(exc)[:500]}
            raise
        finally:
            self.record(Event(
                event_type=event_type,
                agent=agent,
                latency_ms=(time.perf_counter() - start) * 1000,
                success=bool(outcome["success"]),
                failure_mode=outcome.get("failure_mode"),
                metadata=outcome.get("metadata"),
                **fields,
            ))

    @staticmethod
    def classify_failure(exc: Exception) -> str:
        name = type(exc).__name__.lower()
        text = str(exc).lower()
        if "timeout" in name or "timeout" in text:
            return "timeout"
        if "429" in text or "rate" in text:
            return "rate_limit"
        if "json" in name or "parse" in text or "validation" in text:
            return "parse_failure"
        if "budget" in text or "quota" in text:
            return "budget_exceeded"
        return "other"

    def set_index_state(self, collection: str, chunks: int, model: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO index_state VALUES (?, ?, ?, ?)
                ON CONFLICT(collection) DO UPDATE SET chunks=excluded.chunks,
                indexed_at=excluded.indexed_at, model=excluded.model""",
                (collection, chunks, now, model),
            )

    def add_feedback(self, query_id: str, value: int, user_id: str = "anonymous", comment: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(), query_id, user_id, value, comment),
            )

    def dashboard(self, hours: int = 24) -> dict[str, Any]:
        modifier = f"-{int(hours)} hours"
        with self._connect() as conn:
            retrieval = conn.execute(
                """SELECT latency_ms, success, metadata FROM events
                WHERE event_type='retrieval' AND datetime(created_at) >= datetime('now', ?)""", (modifier,)
            ).fetchall()
            failures = conn.execute(
                """SELECT COALESCE(failure_mode,'none') mode, COUNT(*) count FROM events
                WHERE success=0 AND datetime(created_at) >= datetime('now', ?) GROUP BY mode""", (modifier,)
            ).fetchall()
            costs = conn.execute(
                """SELECT agent, user_id, SUM(cost_usd) cost, COUNT(DISTINCT query_id) queries
                FROM events WHERE datetime(created_at) >= datetime('now', ?) GROUP BY agent, user_id""", (modifier,)
            ).fetchall()
            feedback = conn.execute(
                """SELECT value, COUNT(*) count FROM feedback
                WHERE datetime(created_at) >= datetime('now', ?) GROUP BY value""", (modifier,)
            ).fetchall()
            index_state = conn.execute("SELECT * FROM index_state").fetchall()
            timeline = conn.execute(
                """SELECT substr(created_at,1,13) hour, COUNT(*) calls,
                SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) failures, SUM(cost_usd) cost
                FROM events WHERE datetime(created_at) >= datetime('now', ?)
                GROUP BY hour ORDER BY hour""", (modifier,)
            ).fetchall()
        latencies = sorted(float(r["latency_ms"]) for r in retrieval)
        no_hits = sum(1 for r in retrieval if json.loads(r["metadata"] or "{}").get("hit_count", 1) == 0)
        p99 = latencies[min(len(latencies) - 1, int(len(latencies) * .99))] if latencies else 0.0
        return {
            "retrieval_count": len(retrieval),
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
            "p99_latency": p99,
            "no_hit_rate": no_hits / len(retrieval) if retrieval else 0.0,
            "failures": [dict(r) for r in failures],
            "costs": [dict(r) for r in costs],
            "feedback": [dict(r) for r in feedback],
            "index_state": [dict(r) for r in index_state],
            "timeline": [dict(r) for r in timeline],
        }


monitor = Monitor()
