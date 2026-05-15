import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_conn

router = APIRouter()

# Which plans can activate each feature.
# Default plan is 'free'. Set plan='pro'/'team'/'enterprise' manually for alpha users.
PLAN_GATES: dict[str, list[str]] = {
    "optimizer_enabled": ["pro", "team", "enterprise"],
    "budget_enabled":    ["team", "enterprise"],
    "memory_enabled":    ["enterprise"],
}


class SettingsOut(BaseModel):
    plan: str
    optimizer_enabled: bool
    budget_enabled: bool
    memory_enabled: bool
    max_cost_per_run: float
    max_retries: int
    enabled_at: str | None
    baseline_avg_tokens: float | None
    baseline_avg_cost: float | None
    baseline_avg_retries: float | None
    updated_at: str


class SettingsPatch(BaseModel):
    plan: str | None = None
    optimizer_enabled: bool | None = None
    budget_enabled: bool | None = None
    memory_enabled: bool | None = None
    max_cost_per_run: float | None = None
    max_retries: int | None = None


def _row_to_out(row) -> SettingsOut:
    return SettingsOut(
        plan=row["plan"],
        optimizer_enabled=bool(row["optimizer_enabled"]),
        budget_enabled=bool(row["budget_enabled"]),
        memory_enabled=bool(row["memory_enabled"]),
        max_cost_per_run=row["max_cost_per_run"],
        max_retries=row["max_retries"],
        enabled_at=row["enabled_at"],
        baseline_avg_tokens=row["baseline_avg_tokens"],
        baseline_avg_cost=row["baseline_avg_cost"],
        baseline_avg_retries=row["baseline_avg_retries"],
        updated_at=row["updated_at"],
    )


def _capture_baseline(conn) -> tuple[float | None, float | None, float | None]:
    """Snapshot avg tokens/cost/retries from the last 10 analysis reports."""
    rows = conn.execute(
        "SELECT report_json FROM analysis_reports ORDER BY generated_at DESC LIMIT 10"
    ).fetchall()
    if not rows:
        return None, None, None
    tokens, costs, retries = [], [], []
    for r in rows:
        try:
            d = json.loads(r["report_json"])
            tokens.append(d.get("total_input_tokens", 0))
            costs.append(d.get("estimated_total_cost_dollars", 0))
            retries.append(d.get("retry_count", 0))
        except Exception:
            pass
    avg = lambda lst: sum(lst) / len(lst) if lst else None
    return avg(tokens), avg(costs), avg(retries)


@router.get("/settings", response_model=SettingsOut)
def get_settings():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if row is None:
            # Alpha default: 'pro' so all toggles work out of the box
            conn.execute("INSERT INTO settings (id, plan) VALUES (1, 'pro')")
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        # Migration: upgrade existing 'free' installs to 'pro' for alpha period
        if row["plan"] == "free":
            conn.execute("UPDATE settings SET plan = 'pro' WHERE id = 1")
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return _row_to_out(row)


@router.patch("/settings", response_model=SettingsOut)
def patch_settings(body: SettingsPatch):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if row is None:
            conn.execute("INSERT INTO settings (id) VALUES (1)")
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()

        current_plan = body.plan if body.plan is not None else row["plan"]

        # Check plan gates for any feature being turned ON
        toggle_fields = {
            "optimizer_enabled": body.optimizer_enabled,
            "budget_enabled": body.budget_enabled,
            "memory_enabled": body.memory_enabled,
        }
        for field, new_val in toggle_fields.items():
            if new_val is True:
                allowed = PLAN_GATES.get(field, [])
                if current_plan not in allowed:
                    tier_map = {
                        "optimizer_enabled": "Pro ($49/mo)",
                        "budget_enabled": "Team ($149/mo)",
                        "memory_enabled": "Enterprise",
                    }
                    raise HTTPException(
                        status_code=403,
                        detail=f"Upgrade to {tier_map[field]} to enable this feature.",
                    )

        now = datetime.now(timezone.utc).isoformat()

        # Capture baseline snapshot when any toggle goes ON for the first time
        any_newly_enabled = any(
            new_val is True and not bool(row[field])
            for field, new_val in toggle_fields.items()
        )
        baseline_tokens = row["baseline_avg_tokens"]
        baseline_cost = row["baseline_avg_cost"]
        baseline_retries = row["baseline_avg_retries"]
        enabled_at = row["enabled_at"]

        if any_newly_enabled and enabled_at is None:
            baseline_tokens, baseline_cost, baseline_retries = _capture_baseline(conn)
            enabled_at = now

        updates: dict[str, object] = {"updated_at": now}
        if body.plan is not None:
            updates["plan"] = body.plan
        if body.optimizer_enabled is not None:
            updates["optimizer_enabled"] = int(body.optimizer_enabled)
        if body.budget_enabled is not None:
            updates["budget_enabled"] = int(body.budget_enabled)
        if body.memory_enabled is not None:
            updates["memory_enabled"] = int(body.memory_enabled)
        if body.max_cost_per_run is not None:
            updates["max_cost_per_run"] = body.max_cost_per_run
        if body.max_retries is not None:
            updates["max_retries"] = body.max_retries
        if baseline_tokens is not None:
            updates["baseline_avg_tokens"] = baseline_tokens
        if baseline_cost is not None:
            updates["baseline_avg_cost"] = baseline_cost
        if baseline_retries is not None:
            updates["baseline_avg_retries"] = baseline_retries
        if enabled_at is not None:
            updates["enabled_at"] = enabled_at

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE settings SET {set_clause} WHERE id = 1",
            list(updates.values()),
        )

        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return _row_to_out(row)
