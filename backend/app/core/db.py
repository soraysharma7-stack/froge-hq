"""SQLite persistence layer for FROGÉ HQ.

Single async connection (aiosqlite) over the configured DATABASE_URL
(FROGE_DATABASE_URL, default sqlite+aiosqlite:///./froge_hq.db).
Structure stays PostgreSQL-ready: one JSON document table per store plus a
generic key-value events table for the time machine.

Rules: persistence failures never crash the app — they are logged and the
in-memory state keeps working (honest degradation, no fake data loss/save).
"""
from __future__ import annotations

import json
import re
from urllib.parse import unquote

import aiosqlite

from app.config.settings import settings

_conn: aiosqlite.Connection | None = None

_TABLE_RE = re.compile(r"^[a-z_]+$")


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite"):
        path = unquote(url.split("///", 1)[-1]) if "///" in url else "froge_hq.db"
        # "sqlite:////abs/path" keeps its leading slash; "sqlite:///./rel" stays relative
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            path = path.lstrip("/")
        return path or "froge_hq.db"
    return "froge_hq.db"


async def init_db() -> None:
    global _conn
    if _conn is not None:
        return
    _conn = await aiosqlite.connect(_db_path())
    _conn.row_factory = aiosqlite.Row
    await _conn.execute("PRAGMA journal_mode=WAL")
    await _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            table_name TEXT NOT NULL,
            id TEXT NOT NULL,
            data TEXT NOT NULL,
            PRIMARY KEY (table_name, id)
        )
        """
    )
    await _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            type TEXT,
            message TEXT,
            source TEXT,
            severity TEXT,
            mission_id TEXT,
            employee_id TEXT,
            metadata TEXT
        )
        """
    )
    await _conn.commit()


async def close_db() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None


def _check(table: str) -> None:
    if not _TABLE_RE.match(table):
        raise ValueError(f"invalid table name: {table!r}")


async def upsert(table: str, doc_id: str, data: dict) -> None:
    _check(table)
    if _conn is None:
        return
    await _conn.execute(
        "INSERT INTO documents (table_name, id, data) VALUES (?, ?, ?) "
        "ON CONFLICT (table_name, id) DO UPDATE SET data = excluded.data",
        (table, doc_id, json.dumps(data, default=str)),
    )
    await _conn.commit()


async def delete(table: str, doc_id: str) -> None:
    _check(table)
    if _conn is None:
        return
    await _conn.execute(
        "DELETE FROM documents WHERE table_name = ? AND id = ?", (table, doc_id)
    )
    await _conn.commit()


async def load_all(table: str) -> list[dict]:
    _check(table)
    if _conn is None:
        return []
    cursor = await _conn.execute(
        "SELECT data FROM documents WHERE table_name = ?", (table,)
    )
    rows = await cursor.fetchall()
    return [json.loads(row["data"]) for row in rows]


async def append_event(event: dict) -> None:
    if _conn is None:
        return
    await _conn.execute(
        "INSERT INTO events (ts, type, message, source, severity, mission_id, employee_id, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event.get("ts", 0.0),
            event.get("type"),
            event.get("message"),
            event.get("source"),
            event.get("severity"),
            event.get("mission_id"),
            event.get("employee_id"),
            json.dumps(event.get("metadata") or {}, default=str),
        ),
    )
    await _conn.commit()


async def load_events(limit: int = 1000) -> list[dict]:
    if _conn is None:
        return []
    cursor = await _conn.execute(
        "SELECT * FROM events ORDER BY seq DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    return [
        {
            "seq": r["seq"],
            "ts": r["ts"],
            "type": r["type"],
            "message": r["message"],
            "source": r["source"],
            "severity": r["severity"],
            "mission_id": r["mission_id"],
            "employee_id": r["employee_id"],
            "metadata": json.loads(r["metadata"] or "{}"),
        }
        for r in reversed(rows)
    ]
