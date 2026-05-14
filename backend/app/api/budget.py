"""Phase 1.8: Budget Governor — config and event endpoints."""

from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter

from app.db import get_conn
from app.schemas import BudgetConfig, BudgetEvent, BudgetGovernorSummary

router = APIRouter()

_DEFAULT_CONFIG = BudgetConfig()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _store_event(conn, event: BudgetEvent) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO budget_events
           (event_id, session_id, task_id, event_type, reason,
            cost_at_block, retries_at_block, budget_limit, retry_limit, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            event.event_id,
            event.session_id,
            event.task_id,
            event.event_type,
            event.reason,
            event.cost_at_block,
            event.retries_at_block,
            event.budget_limit,
            event.retry_limit,
            event.created_at or _utc_now(),
        ),
    )


def _row_to_event(row) -> BudgetEvent:
    return BudgetEvent(
        event_id=row["event_id"],
        session_id=row["session_id"],
        task_id=row["task_id"],
        event_type=row["event_type"],
        reason=row["reason"],
        cost_at_block=row["cost_at_block"],
        retries_at_block=row["retries_at_block"],
        budget_limit=row["budget_limit"],
        retry_limit=row["retry_limit"],
        created_at=row["created_at"],
    )


@router.get("/budget/config", response_model=BudgetConfig)
def get_budget_config() -> BudgetConfig:
    """Return the active budget configuration. Defaults if not yet set."""
    return _DEFAULT_CONFIG


@router.post("/budget/config", response_model=BudgetConfig)
def update_budget_config(config: BudgetConfig) -> BudgetConfig:
    """Update budget configuration. Changes apply to new sessions immediately."""
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = config
    return _DEFAULT_CONFIG


@router.post("/budget/events", response_model=BudgetEvent)
def record_budget_event(event: BudgetEvent) -> BudgetEvent:
    """Record a budget enforcement event (called by the SDK hook when a run is blocked)."""
    if not event.event_id:
        event.event_id = f"bev_{uuid4().hex[:12]}"
    if not event.created_at:
        event.created_at = _utc_now()
    with get_conn() as conn:
        _store_event(conn, event)
    return event


@router.get("/budget/events", response_model=list[BudgetEvent])
def list_budget_events(session_id: str | None = None, limit: int = 50) -> list[BudgetEvent]:
    with get_conn() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM budget_events WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM budget_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [_row_to_event(r) for r in rows]


@router.get("/budget/summary", response_model=BudgetGovernorSummary)
def get_budget_summary() -> BudgetGovernorSummary:
    """Return a summary of budget enforcement activity across all sessions."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM budget_events ORDER BY created_at DESC LIMIT 100").fetchall()
        events = [_row_to_event(r) for r in rows]

        blocks_by_type: dict[str, int] = {}
        total_saved = 0.0
        for ev in events:
            blocks_by_type[ev.event_type] = blocks_by_type.get(ev.event_type, 0) + 1
            # Estimate savings: if budget was $0.10 and we blocked at $0.05, saved ~$0.05
            if ev.budget_limit and ev.cost_at_block:
                saved = max(0.0, ev.budget_limit - ev.cost_at_block)
                total_saved += saved

        return BudgetGovernorSummary(
            total_blocked_runs=len(events),
            total_saved_dollars=round(total_saved, 6),
            blocks_by_type=blocks_by_type,
            recent_events=events[:10],
            config=_DEFAULT_CONFIG,
        )
