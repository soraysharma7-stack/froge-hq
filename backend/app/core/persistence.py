"""Persistence bridges — keep module stores in memory AND durable in SQLite.

Each module registers a saver (called after mutations) and a restorer
(called once at startup). Saves are best-effort: a DB error is logged, not
raised, so the app degrades honestly instead of crashing.
"""
from __future__ import annotations

import asyncio
import logging

from app.core import db

log = logging.getLogger("froge.persistence")

TABLE_MISSIONS = "missions"
TABLE_ARTIFACTS = "artifacts"
TABLE_MEMORIES = "memories"
TABLE_DECISIONS = "decisions"
TABLE_APPROVALS = "approvals"
TABLE_AUDIT = "audit"
TABLE_NOTIFICATIONS = "notifications"
TABLE_REPUTATION = "reputation"
TABLE_KNOWLEDGE = "knowledge"


def save(table: str, doc_id: str, data: dict) -> None:
    """Fire-and-forget durable save of one document."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(_save_safe(table, doc_id, data))


async def _save_safe(table: str, doc_id: str, data: dict) -> None:
    try:
        await db.upsert(table, doc_id, data)
    except Exception as exc:  # honest degradation — app keeps running in-memory
        log.warning("persistence save failed (%s/%s): %s", table, doc_id, exc)


def remove(table: str, doc_id: str) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(db.delete(table, doc_id))


async def restore_all() -> None:
    """Load durable state back into the in-memory module stores at startup."""
    from app.missions import manager as missions
    from app.artifacts import library as artifacts
    from app.memory import vault as memory
    from app.decisions import adr
    from app.approvals import engine as approvals
    from app.audit import log as audit
    from app.notifications import center as notifications
    from app.reputation import tracker as reputation
    from app.knowledge import graph as knowledge

    restored: dict[str, int] = {}

    for doc in await db.load_all(TABLE_MISSIONS):
        missions.restore(doc)
    restored["missions"] = len(await db.load_all(TABLE_MISSIONS))

    for doc in await db.load_all(TABLE_ARTIFACTS):
        artifacts._ARTIFACTS[doc["id"]] = doc
    restored["artifacts"] = len(await db.load_all(TABLE_ARTIFACTS))

    for doc in await db.load_all(TABLE_MEMORIES):
        memory._MEMORIES[doc["id"]] = doc
    restored["memories"] = len(await db.load_all(TABLE_MEMORIES))

    for doc in await db.load_all(TABLE_DECISIONS):
        adr.restore(doc)
    restored["decisions"] = len(await db.load_all(TABLE_DECISIONS))

    for doc in await db.load_all(TABLE_APPROVALS):
        approvals.restore(doc)
    restored["approvals"] = len(await db.load_all(TABLE_APPROVALS))

    for doc in await db.load_all(TABLE_AUDIT):
        audit.restore(doc)
    restored["audit"] = len(await db.load_all(TABLE_AUDIT))

    for doc in await db.load_all(TABLE_NOTIFICATIONS):
        notifications.restore(doc)
    restored["notifications"] = len(await db.load_all(TABLE_NOTIFICATIONS))

    for doc in await db.load_all(TABLE_REPUTATION):
        reputation.restore(doc)
    restored["reputation"] = len(await db.load_all(TABLE_REPUTATION))

    for doc in await db.load_all(TABLE_KNOWLEDGE):
        knowledge.restore(doc)
    restored["knowledge"] = len(await db.load_all(TABLE_KNOWLEDGE))

    from app import auth
    account_docs = await db.load_all(auth.TABLE_ACCOUNTS)
    for doc in account_docs:
        auth.restore_account(doc)
    restored["accounts"] = len(account_docs)

    log.info("persistence restored: %s", restored)
