import json
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Model pricing per million tokens (USD)
MODEL_PRICING = {
    "claude-opus-4-5":    {"input": 15.0,  "output": 75.0,  "cache_read": 1.50,  "cache_write": 18.75},
    "claude-sonnet-4-6":  {"input": 3.0,   "output": 15.0,  "cache_read": 0.30,  "cache_write": 3.75},
    "claude-sonnet-4-5":  {"input": 3.0,   "output": 15.0,  "cache_read": 0.30,  "cache_write": 3.75},
    "claude-haiku-4-5":   {"input": 0.8,   "output": 4.0,   "cache_read": 0.08,  "cache_write": 1.0},
    "claude-3-5-sonnet":  {"input": 3.0,   "output": 15.0,  "cache_read": 0.30,  "cache_write": 3.75},
    "claude-3-5-haiku":   {"input": 0.8,   "output": 4.0,   "cache_read": 0.08,  "cache_write": 1.0},
    "claude-3-opus":      {"input": 15.0,  "output": 75.0,  "cache_read": 1.50,  "cache_write": 18.75},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75}


def calculate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read_tokens: int = 0, cache_write_tokens: int = 0) -> float:
    pricing = next((v for k, v in MODEL_PRICING.items() if model and k in model), DEFAULT_PRICING)
    return (
        input_tokens      * pricing["input"]       / 1_000_000 +
        output_tokens     * pricing["output"]      / 1_000_000 +
        cache_read_tokens * pricing["cache_read"]  / 1_000_000 +
        cache_write_tokens* pricing["cache_write"] / 1_000_000
    )


def parse_transcript(transcript_path: str) -> dict:
    """Read Claude Code transcript and extract token usage, cost and model call count."""
    try:
        p = Path(transcript_path)
        if not p.exists():
            return {}
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        total_input = total_output = total_cache_read = total_cache_write = 0
        total_cost = 0.0
        model_calls = 0
        model = "unknown"
        for line in lines:
            try:
                d = json.loads(line)
                if d.get("type") != "assistant":
                    continue
                msg = d.get("message") or {}
                usage = msg.get("usage") or {}
                if not usage:
                    continue
                m = msg.get("model") or model
                if m and m != "unknown":
                    model = m
                inp   = int(usage.get("input_tokens", 0) or 0)
                out   = int(usage.get("output_tokens", 0) or 0)
                cr    = int(usage.get("cache_read_input_tokens", 0) or 0)
                cw    = int(usage.get("cache_creation_input_tokens", 0) or 0)
                total_input       += inp
                total_output      += out
                total_cache_read  += cr
                total_cache_write += cw
                total_cost        += calculate_cost(model, inp, out, cr, cw)
                model_calls       += 1
            except Exception:
                continue
        # Repeated CTX% = cache_read / total context size per call
        total_context = total_input + total_cache_read + total_cache_write
        repeated_pct = round((total_cache_read / total_context) * 100, 2) if total_context else 0.0

        return {
            "model": model,
            "model_calls": model_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache_read,
            "total_cache_write_tokens": total_cache_write,
            "estimated_cost_usd": round(total_cost, 6),
            "total_context_tokens": total_context,
            "repeated_tokens": total_cache_read,
            "repeated_context_percent": repeated_pct,
        }
    except Exception:
        return {}

from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_text, redact_value
from agent_runtime_layer.trace import TraceEvent


CLAUDE_HOOK_EVENTS = [
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "Stop",
    "SessionEnd",
]
DEFAULT_STATE_DIR = Path(".agent-runtime") / "claude-code"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def config_path(repo_path: Path, global_install: bool = False) -> Path:
    if global_install:
        return Path.home() / ".claude" / "settings.json"
    return repo_path / ".claude" / "settings.local.json"


def state_path(repo_path: Path) -> Path:
    return repo_path / DEFAULT_STATE_DIR / "state.json"


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def prompt_text(payload: dict) -> str:
    value = payload.get("prompt") or payload.get("user_prompt")
    if isinstance(value, str) and value.strip():
        return value
    return "Claude Code turn"


def compact_preview(value: object, limit: int = 4000) -> object:
    if isinstance(value, str):
        return value if len(value) <= limit else f"{value[:limit]}\n...[truncated {len(value) - limit} chars]"
    return value


def hook_command(event_name: str, base_url: str, project_id: str | None = None) -> str:
    if sys.platform == "win32":
        parts = ["agent-runtime", "--base-url", f"'{base_url}'", "claude-hook", "--event", f"'{event_name}'"]
        if project_id:
            parts.extend(["--project", f"'{project_id}'"])
    else:
        parts = ["agent-runtime", "--base-url", shlex.quote(base_url), "claude-hook", "--event", shlex.quote(event_name)]
        if project_id:
            parts.extend(["--project", shlex.quote(project_id)])
    return " ".join(parts)


def managed_hook(event_name: str, base_url: str, project_id: str | None = None) -> dict:
    return {
        "type": "command",
        "command": hook_command(event_name, base_url, project_id),
        "agentium_managed": True,
        "agentium_integration": "claude-code",
    }


def managed_entry(event_name: str, base_url: str, project_id: str | None = None) -> dict:
    entry = {
        "hooks": [managed_hook(event_name, base_url, project_id)],
        "agentium_managed": True,
        "agentium_integration": "claude-code",
    }
    if event_name in {"PreToolUse", "PostToolUse", "PostToolUseFailure"}:
        entry["matcher"] = "*"
    return entry


def install_claude_hooks(repo_path: Path, base_url: str = "http://localhost:8000/api", project_id: str | None = None, global_install: bool = False) -> Path:
    path = config_path(repo_path, global_install)
    config = read_json(path, {})
    hooks = config.setdefault("hooks", {})
    for event_name in CLAUDE_HOOK_EVENTS:
        entries = hooks.setdefault(event_name, [])
        entries = [entry for entry in entries if entry.get("agentium_integration") != "claude-code"]
        entries.append(managed_entry(event_name, base_url, project_id))
        hooks[event_name] = entries
    write_json(path, config)
    return path


def uninstall_claude_hooks(repo_path: Path, global_install: bool = False) -> Path:
    path = config_path(repo_path, global_install)
    config = read_json(path, {})
    hooks = config.get("hooks", {})
    for event_name in list(hooks):
        hooks[event_name] = [entry for entry in hooks[event_name] if entry.get("agentium_integration") != "claude-code"]
        if not hooks[event_name]:
            hooks.pop(event_name)
    if hooks:
        config["hooks"] = hooks
    else:
        config.pop("hooks", None)
    write_json(path, config)
    return path


def claude_hook_status(repo_path: Path, global_install: bool = False) -> dict:
    path = config_path(repo_path, global_install)
    config = read_json(path, {})
    hooks = config.get("hooks", {})
    installed_events = []
    for event_name in CLAUDE_HOOK_EVENTS:
        if any(entry.get("agentium_integration") == "claude-code" for entry in hooks.get(event_name, [])):
            installed_events.append(event_name)
    return {
        "integration": "claude-code",
        "config_path": str(path),
        "installed": set(installed_events) == set(CLAUDE_HOOK_EVENTS),
        "installed_events": installed_events,
        "missing_events": [event for event in CLAUDE_HOOK_EVENTS if event not in installed_events],
    }


@dataclass
class ClaudeHookResult:
    event_name: str
    task_id: str | None
    emitted_events: int
    skipped: bool = False
    reason: str | None = None


class ClaudeHookCollector:
    def __init__(
        self,
        repo_path: Path | str = ".",
        base_url: str = "http://localhost:8000/api",
        project_id: str | None = None,
        client: AgentRuntimeClient | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.project_id = project_id or self.repo_path.name or "default"
        self.client = client or AgentRuntimeClient(base_url)
        self.state_file = state_path(self.repo_path)

    def load_state(self) -> dict:
        return read_json(self.state_file, {"sessions": {}, "turns": {}})

    def save_state(self, state: dict) -> None:
        write_json(self.state_file, state)

    def state_key(self, payload: dict) -> str:
        return f"{payload.get('session_id') or 'unknown_session'}:{payload.get('turn_id') or 'active_turn'}"

    def task_span_id(self, state: dict, payload: dict) -> str:
        return state.get("turns", {}).get(self.state_key(payload), {}).get("task_span_id", f"span_task_{uuid4().hex[:8]}")

    def active_task_id(self, state: dict, payload: dict) -> str | None:
        turn = state.get("turns", {}).get(self.state_key(payload))
        if turn:
            return turn.get("task_id")
        session = state.get("sessions", {}).get(str(payload.get("session_id") or "unknown_session"))
        return session.get("active_task_id") if session else None

    def add_event(self, task_id: str, event_type: str, span_id: str, name: str, attributes=None, payload=None, parent_span_id=None) -> None:
        self.client.add_event(
            TraceEvent(
                task_id=task_id,
                event_type=event_type,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                attributes=redact_value(attributes or {}),
                payload=redact_value(payload or {}),
            )
        )

    def create_turn_task(self, state: dict, payload: dict) -> str:
        session_id = str(payload.get("session_id") or "unknown_session")
        goal = redact_text(prompt_text(payload))
        task_id = self.client.create_task(goal=goal, project_id=self.project_id, agent_type="claude-code")
        state.setdefault("turns", {})[self.state_key(payload)] = {
            "task_id": task_id,
            "task_span_id": f"span_task_{uuid4().hex[:8]}",
            "started_at": utc_now(),
        }
        state.setdefault("sessions", {}).setdefault(session_id, {})["active_task_id"] = task_id
        return task_id

    def handle(self, event_name: str, payload: dict) -> ClaudeHookResult:
        state = self.load_state()
        try:
            if event_name == "SessionStart":
                session_id = str(payload.get("session_id") or "unknown_session")
                state.setdefault("sessions", {}).setdefault(session_id, {})["started_at"] = utc_now()
                state["sessions"][session_id]["cwd"] = payload.get("cwd")
                self.save_state(state)
                return ClaudeHookResult(event_name, None, 0)

            if event_name == "UserPromptSubmit":
                task_id = self.create_turn_task(state, payload)
                task_span_id = self.task_span_id(state, payload)
                prompt = redact_text(prompt_text(payload))
                transcript_path = payload.get("transcript_path")
                # Store transcript_path so Stop handler can read it
                state.setdefault("turns", {})[self.state_key(payload)]["transcript_path"] = transcript_path
                self.add_event(
                    task_id,
                    "task_start",
                    task_span_id,
                    "claude_code_turn_start",
                    attributes={
                        "integration": "claude-code",
                        "session_id": payload.get("session_id"),
                        "cwd": payload.get("cwd") or payload.get("CLAUDE_PROJECT_DIR"),
                        "transcript_path": transcript_path,
                    },
                    payload={"goal": prompt, "agent_type": "claude-code"},
                )
                self.add_event(
                    task_id,
                    "context_snapshot",
                    f"span_context_{uuid4().hex[:8]}",
                    "claude_code_user_prompt",
                    attributes={"context_kind": "user_prompt", "source": "claude_code_hook", "size_tokens": max(1, len(prompt.split()))},
                    payload={"prompt_preview": compact_preview(prompt)},
                    parent_span_id=task_span_id,
                )
                self.save_state(state)
                return ClaudeHookResult(event_name, task_id, 2)

            task_id = self.active_task_id(state, payload)
            if not task_id:
                return ClaudeHookResult(event_name, None, 0, skipped=True, reason="No active Claude Code task for hook event.")
            task_span_id = self.task_span_id(state, payload)

            if event_name == "PreToolUse":
                tool_use_id = str(payload.get("tool_use_id") or uuid4().hex[:8])
                self.add_event(
                    task_id,
                    "tool_call_start",
                    f"span_claude_tool_{tool_use_id[-8:]}",
                    f"claude_code_{payload.get('tool_name', 'tool')}",
                    attributes={"integration": "claude-code", "tool_name": payload.get("tool_name"), "tool_use_id": tool_use_id, "cwd": payload.get("cwd")},
                    payload={"tool_input": compact_preview(redact_value(payload.get("tool_input", {})))},
                    parent_span_id=task_span_id,
                )
                return ClaudeHookResult(event_name, task_id, 1)

            if event_name in {"PostToolUse", "PostToolUseFailure"}:
                tool_use_id = str(payload.get("tool_use_id") or uuid4().hex[:8])
                span_id = f"span_claude_tool_{tool_use_id[-8:]}"
                tool_name = str(payload.get("tool_name") or "tool")
                status = "failed" if event_name == "PostToolUseFailure" else "success"
                emitted = 1
                self.add_event(
                    task_id,
                    "tool_call_end",
                    span_id,
                    f"claude_code_{tool_name}_end",
                    attributes={"integration": "claude-code", "tool_name": tool_name, "tool_use_id": tool_use_id, "status": status, "latency_ms": int(payload.get("duration_ms", 0) or 0)},
                    payload={"tool_response": compact_preview(redact_value(payload.get("tool_response", payload.get("error", {}))))},
                    parent_span_id=task_span_id,
                )
                if status == "failed":
                    self.add_event(task_id, "error_event", f"span_error_{uuid4().hex[:8]}", "claude_code_tool_failure", attributes={"integration": "claude-code", "tool_name": tool_name}, payload={"error": redact_value(payload.get("error", payload.get("tool_response", {})))}, parent_span_id=span_id)
                    emitted += 1
                if tool_name.lower() == "bash":
                    self.add_event(task_id, "terminal_event", f"span_terminal_{uuid4().hex[:8]}", "claude_code_terminal_output", attributes={"integration": "claude-code", "command": (payload.get("tool_input") or {}).get("command") if isinstance(payload.get("tool_input"), dict) else None, "duration_ms": int(payload.get("duration_ms", 0) or 0)}, payload={"tool_response": compact_preview(redact_value(payload.get("tool_response", {})))}, parent_span_id=span_id)
                    emitted += 1
                if tool_name.lower() in {"edit", "write"}:
                    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
                    self.add_event(task_id, "file_event", f"span_file_{uuid4().hex[:8]}", "claude_code_file_change", attributes={"integration": "claude-code", "operation": "write", "path": tool_input.get("file_path") or tool_input.get("path"), "content_stored": False}, parent_span_id=span_id)
                    emitted += 1
                return ClaudeHookResult(event_name, task_id, emitted)

            if event_name in {"Stop", "SessionEnd"}:
                # Read transcript to get real token/cost/model data
                turn = state.get("turns", {}).get(self.state_key(payload), {})
                transcript_path = turn.get("transcript_path") or payload.get("transcript_path")
                metrics = parse_transcript(transcript_path) if transcript_path else {}
                self.add_event(
                    task_id,
                    "task_end",
                    task_span_id,
                    "claude_code_turn_end",
                    attributes={
                        "integration": "claude-code",
                        "model": metrics.get("model", "unknown"),
                        "model_calls": metrics.get("model_calls", 0),
                        "total_input_tokens": metrics.get("total_input_tokens", 0),
                        "total_output_tokens": metrics.get("total_output_tokens", 0),
                        "total_cache_read_tokens": metrics.get("total_cache_read_tokens", 0),
                        "total_cache_write_tokens": metrics.get("total_cache_write_tokens", 0),
                        "estimated_cost_usd": metrics.get("estimated_cost_usd", 0.0),
                        "total_context_tokens": metrics.get("total_context_tokens", 0),
                        "repeated_tokens": metrics.get("repeated_tokens", 0),
                        "repeated_context_percent": metrics.get("repeated_context_percent", 0.0),
                    },
                    payload={
                        "status": "completed",
                        "summary": f"Claude Code session: {metrics.get('model_calls', 0)} model calls, "
                                   f"{metrics.get('total_input_tokens', 0) + metrics.get('total_output_tokens', 0)} total tokens, "
                                   f"${metrics.get('estimated_cost_usd', 0.0):.4f} cost",
                    },
                )
                return ClaudeHookResult(event_name, task_id, 1)

            return ClaudeHookResult(event_name, task_id, 0, skipped=True)
        except Exception as exc:
            return ClaudeHookResult(event_name, None, 0, skipped=True, reason=str(exc))


def run_claude_hook(event_name: str, repo_path: Path, base_url: str, project_id: str | None = None) -> ClaudeHookResult:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        return ClaudeHookResult(event_name, None, 0, skipped=True, reason=str(exc))
    return ClaudeHookCollector(repo_path=repo_path, base_url=base_url, project_id=project_id).handle(event_name, payload)
