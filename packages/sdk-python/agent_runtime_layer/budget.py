"""Phase 1.8: Budget Governor — session cost and retry state tracker.

Reads .agentium/config.yaml and enforces per-run budget caps and retry limits.
Used by Claude Code and Codex hook handlers to block runaway runs.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_CONFIG = {
    "max_cost_per_run": 0.10,
    "max_retries_per_task": 5,
    "alert_threshold": 0.05,
    "token_limit_per_call": 200000,
    "enabled": True,
}


@dataclass
class BudgetState:
    session_id: str
    task_id: str | None = None
    cost: float = 0.0
    retries: int = 0
    blocked: bool = False
    block_reason: str = ""
    started_at: float = field(default_factory=time.time)


class BudgetGovernor:
    """Session-scoped budget governor. One instance per agent session."""

    def __init__(
        self,
        repo_path: Path | str = ".",
        base_url: str = "http://localhost:8000/api",
        session_id: str | None = None,
    ) -> None:
        self.repo_path = Path(repo_path)
        self.base_url = base_url
        self.session_id = session_id or f"bsess_{uuid4().hex[:12]}"
        self._config = self._load_config()
        self._state = BudgetState(session_id=self.session_id)

    def _load_config(self) -> dict[str, Any]:
        """Load .agentium/config.yaml or fall back to defaults."""
        config_path = self.repo_path / ".agentium" / "config.yaml"
        if config_path.exists():
            try:
                import yaml  # type: ignore[import]
                with open(config_path, encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                return {**DEFAULT_CONFIG, **loaded}
            except Exception:
                pass
        # Try JSON fallback
        json_path = self.repo_path / ".agentium" / "config.json"
        if json_path.exists():
            try:
                with open(json_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                return {**DEFAULT_CONFIG, **loaded}
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled", True))

    @property
    def max_cost(self) -> float:
        return float(self._config.get("max_cost_per_run", 0.10))

    @property
    def max_retries(self) -> int:
        return int(self._config.get("max_retries_per_task", 5))

    @property
    def alert_threshold(self) -> float:
        return float(self._config.get("alert_threshold", 0.05))

    def set_task(self, task_id: str) -> None:
        self._state.task_id = task_id

    def add_cost(self, cost_dollars: float) -> None:
        self._state.cost += cost_dollars

    def increment_retry(self) -> None:
        self._state.retries += 1

    def check(self) -> tuple[bool, str]:
        """Check if current session is within budget and retry limits.
        Returns (allowed: bool, reason: str).
        """
        if not self.enabled:
            return True, ""

        if self._state.cost >= self.max_cost:
            reason = (
                f"Budget cap reached: ${self._state.cost:.4f} >= ${self.max_cost:.4f}. "
                f"Run terminated by Agentium Budget Governor."
            )
            self._state.blocked = True
            self._state.block_reason = reason
            self._report_block("budget_cap", reason)
            return False, reason

        if self._state.retries >= self.max_retries:
            reason = (
                f"Retry limit reached: {self._state.retries} >= {self.max_retries} retries. "
                f"Run terminated by Agentium Budget Governor."
            )
            self._state.blocked = True
            self._state.block_reason = reason
            self._report_block("retry_limit", reason)
            return False, reason

        if self._state.cost >= self.alert_threshold and self._state.cost < self.max_cost:
            # Alert but don't block
            pass

        return True, ""

    def _report_block(self, event_type: str, reason: str) -> None:
        """Report a budget block event to the backend API."""
        try:
            import urllib.request
            payload = json.dumps({
                "event_id": f"bev_{uuid4().hex[:12]}",
                "session_id": self.session_id,
                "task_id": self._state.task_id,
                "event_type": event_type,
                "reason": reason,
                "cost_at_block": self._state.cost,
                "retries_at_block": self._state.retries,
                "budget_limit": self.max_cost,
                "retry_limit": self.max_retries,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/budget/events",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass  # Never block the agent because of reporting failures

    @property
    def current_cost(self) -> float:
        return self._state.cost

    @property
    def current_retries(self) -> int:
        return self._state.retries

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "cost": self._state.cost,
            "retries": self._state.retries,
            "blocked": self._state.blocked,
            "block_reason": self._state.block_reason,
            "max_cost": self.max_cost,
            "max_retries": self.max_retries,
        }


def write_default_config(repo_path: Path | str = ".") -> Path:
    """Write a default .agentium/config.yaml to the given repo path."""
    config_dir = Path(repo_path) / ".agentium"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    if not config_path.exists():
        config_path.write_text(
            "# Agentium Phase 1.8 Budget Governor configuration\n"
            "# All settings apply per agent session.\n\n"
            "max_cost_per_run: 0.10        # Stop run if cost exceeds this (dollars)\n"
            "max_retries_per_task: 5       # Stop run after this many retries\n"
            "alert_threshold: 0.05         # Log a warning at this cost (dollars)\n"
            "token_limit_per_call: 200000  # Warn if a single call exceeds this token count\n"
            "enabled: true                 # Set to false to disable all budget enforcement\n",
            encoding="utf-8",
        )
    return config_path
