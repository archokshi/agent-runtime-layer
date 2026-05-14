"""Phase 1.9: Agent Context Fabric — context memory endpoints."""

from fastapi import APIRouter

from app.db import get_conn
from app.schemas import ContextMemoryEntry, ContextMemorySummary

router = APIRouter()


def _row_to_entry(row) -> ContextMemoryEntry:
    return ContextMemoryEntry(
        fingerprint=row["fingerprint"],
        content_type=row["content_type"],
        token_count=row["token_count"],
        source_repo=row["source_repo"],
        agent_type=row["agent_type"],
        first_seen_at=row["first_seen_at"],
        last_seen_at=row["last_seen_at"],
        hit_count=row["hit_count"],
        cache_savings_dollars=row["cache_savings_dollars"],
    )


@router.get("/context-memory/summary", response_model=ContextMemorySummary)
def get_context_memory_summary() -> ContextMemorySummary:
    """Return a summary of the context memory fabric — stable blocks seen, hits, savings."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM context_memory ORDER BY hit_count DESC LIMIT 20"
        ).fetchall()
        entries = [_row_to_entry(r) for r in rows]

        totals = conn.execute(
            "SELECT COUNT(*) as cnt, SUM(token_count) as tok, SUM(hit_count) as hits, SUM(cache_savings_dollars) as saved FROM context_memory"
        ).fetchone()

        total_entries = totals["cnt"] or 0
        total_tokens = totals["tok"] or 0
        total_hits = totals["hits"] or 0
        total_saved = totals["saved"] or 0.0

        evidence_quality = "measured" if total_hits > 0 else "missing"
        msg = (
            f"{total_entries} stable context blocks memorized across {total_hits} hits. "
            f"Total saved: ${total_saved:.4f}."
            if total_entries > 0
            else "No context blocks memorized yet. Start the Agentium proxy to begin capturing stable context."
        )

        return ContextMemorySummary(
            total_entries=total_entries,
            total_tokens_memorized=total_tokens,
            total_hit_count=total_hits,
            total_cache_savings_dollars=round(total_saved, 6),
            top_entries=entries,
            evidence_quality=evidence_quality,
            message=msg,
        )


@router.get("/context-memory", response_model=list[ContextMemoryEntry])
def list_context_memory(limit: int = 50) -> list[ContextMemoryEntry]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM context_memory ORDER BY hit_count DESC, last_seen_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_entry(r) for r in rows]


@router.post("/context-memory", response_model=ContextMemoryEntry)
def upsert_context_memory_entry(entry: ContextMemoryEntry) -> ContextMemoryEntry:
    """Upsert a context memory entry. Called by the proxy when it detects a stable block."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT hit_count, cache_savings_dollars, first_seen_at FROM context_memory WHERE fingerprint = ?",
            (entry.fingerprint,),
        ).fetchone()

        if existing:
            new_hits = existing["hit_count"] + 1
            new_savings = existing["cache_savings_dollars"] + entry.cache_savings_dollars
            conn.execute(
                """UPDATE context_memory
                   SET hit_count=?, last_seen_at=?, cache_savings_dollars=?,
                       content_type=?, token_count=?, source_repo=?, agent_type=?
                   WHERE fingerprint=?""",
                (new_hits, now, new_savings, entry.content_type,
                 entry.token_count, entry.source_repo, entry.agent_type, entry.fingerprint),
            )
            entry.hit_count = new_hits
            entry.cache_savings_dollars = new_savings
            entry.first_seen_at = existing["first_seen_at"]
        else:
            conn.execute(
                """INSERT INTO context_memory
                   (fingerprint, content_type, token_count, source_repo, agent_type,
                    first_seen_at, last_seen_at, hit_count, cache_savings_dollars)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (entry.fingerprint, entry.content_type, entry.token_count,
                 entry.source_repo, entry.agent_type, now, now,
                 entry.hit_count, entry.cache_savings_dollars),
            )
            entry.first_seen_at = now
        entry.last_seen_at = now
        return entry


@router.delete("/context-memory/{fingerprint}", response_model=dict)
def delete_context_memory_entry(fingerprint: str) -> dict:
    with get_conn() as conn:
        conn.execute("DELETE FROM context_memory WHERE fingerprint = ?", (fingerprint,))
    return {"deleted": fingerprint}
