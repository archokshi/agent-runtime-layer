import json
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_text, redact_value
from agent_runtime_layer.trace import TraceEvent


AGENTIUM_MARKER = "agent-runtime-layer"
CODEX_HOOK_EVENTS = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"]
DEFAULT_STATE_DIR = Path(".agent-runtime") / "codex"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def repo_config_path(repo_path: Path) -> Path:
    return repo_path / ".codex" / "hooks.json"


def repo_toml_config_path(repo_path: Path) -> Path:
    return repo_path / ".codex" / "config.toml"


def global_codex_dir(home_dir: Path | None = None) -> Path:
    return (home_dir or Path.home()) / ".codex"


def global_config_path(home_dir: Path | None = None) -> Path:
    return global_codex_dir(home_dir) / "hooks.json"


def global_toml_config_path(home_dir: Path | None = None) -> Path:
    return global_codex_dir(home_dir) / "config.toml"


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
    for key in ("prompt", "user_prompt", "input"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    message = payload.get("message")
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "\n".join(parts)
    return "Codex turn"


def compact_preview(value: object, limit: int = 4000) -> object:
    if isinstance(value, str):
        return value if len(value) <= limit else f"{value[:limit]}\n...[truncated {len(value) - limit} chars]"
    return value


def strip_markdown_links(value: str) -> str:
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)


def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def source_tree_sdk_path(repo_path: Path) -> Path | None:
    sdk_path = repo_path.resolve() / "packages" / "sdk-python"
    cli_path = sdk_path / "agent_runtime_layer" / "cli.py"
    return sdk_path if cli_path.exists() else None


def source_tree_codex_hook_command(
    repo_path: Path,
    event_name: str,
    base_url: str,
    project_id: str | None = None,
) -> str | None:
    sdk_path = source_tree_sdk_path(repo_path)
    if not sdk_path:
        return None
    python_path = Path(sys.executable).resolve()
    if sys.platform == "win32":
        python_args = [
            "-m agent_runtime_layer.cli",
            f"--base-url {ps_single_quote(base_url)}",
            "codex-hook",
            f"--event {ps_single_quote(event_name)}",
        ]
        if project_id:
            python_args.append(f"--project {ps_single_quote(project_id)}")
        command_parts = [
            f"`$env:PYTHONPATH={ps_single_quote(str(sdk_path))}",
            f"& {ps_single_quote(str(python_path))} {' '.join(python_args)}",
        ]
        powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        return (
            f"\"{powershell}\" -NoProfile -ExecutionPolicy Bypass "
            f"-Command \"{'; '.join(command_parts)}\""
        )
    else:
        # macOS / Linux: use bash with PYTHONPATH set inline
        parts = [
            f"PYTHONPATH={shlex.quote(str(sdk_path))}",
            shlex.quote(str(python_path)),
            "-m agent_runtime_layer.cli",
            f"--base-url {shlex.quote(base_url)}",
            "codex-hook",
            f"--event {shlex.quote(event_name)}",
        ]
        if project_id:
            parts.append(f"--project {shlex.quote(project_id)}")
        return " ".join(parts)


def codex_hook_command(
    event_name: str,
    base_url: str,
    project_id: str | None = None,
    repo_path: Path | None = None,
    prefer_source_tree: bool = False,
) -> str:
    if prefer_source_tree and repo_path:
        source_command = source_tree_codex_hook_command(repo_path, event_name, base_url, project_id)
        if source_command:
            return source_command
    parts = ["agent-runtime", "--base-url", base_url, "codex-hook", "--event", event_name]
    if project_id:
        parts.extend(["--project", project_id])
    return " ".join(parts)


def agentium_hook_entry(
    event_name: str,
    base_url: str,
    project_id: str | None = None,
    repo_path: Path | None = None,
    prefer_source_tree: bool = False,
) -> dict:
    return {
        "type": "command",
        "command": codex_hook_command(event_name, base_url, project_id, repo_path, prefer_source_tree),
        "agentium_managed": True,
        "agentium_integration": "codex",
        "statusMessage": f"Agent Runtime capture: {event_name}",
    }


def agentium_matcher_group(
    event_name: str,
    base_url: str,
    project_id: str | None = None,
    repo_path: Path | None = None,
    prefer_source_tree: bool = False,
) -> dict:
    group = {
        "hooks": [agentium_hook_entry(event_name, base_url, project_id, repo_path, prefer_source_tree)],
        "agentium_managed": True,
        "agentium_integration": "codex",
    }
    if event_name in {"SessionStart", "PreToolUse", "PostToolUse"}:
        group["matcher"] = "*" if event_name != "SessionStart" else "startup|resume|clear"
    return group


def enable_codex_hooks_feature(path: Path) -> Path:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    required_flags = ["hooks = true"]
    if all(flag in existing for flag in required_flags):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    addition = "\n" if existing and not existing.endswith("\n") else ""
    if "[features]" not in existing:
        addition += "[features]\n"
    for flag in required_flags:
        if flag not in existing and flag not in addition:
            addition += f"{flag}\n"
    path.write_text(existing + addition, encoding="utf-8")
    return path


def install_codex_hooks(
    repo_path: Path,
    base_url: str = "http://localhost:8000/api",
    project_id: str | None = None,
    global_install: bool = False,
    home_dir: Path | None = None,
) -> Path:
    repo_path = repo_path.resolve()
    config_path = global_config_path(home_dir) if global_install else repo_config_path(repo_path)
    config = read_json(config_path, {})
    hooks = config.setdefault("hooks", {})
    for event_name in CODEX_HOOK_EVENTS:
        entries = hooks.setdefault(event_name, [])
        entries = [entry for entry in entries if entry.get("agentium_integration") != "codex"]
        entries.append(
            agentium_matcher_group(
                event_name,
                base_url,
                project_id,
                repo_path=repo_path,
                prefer_source_tree=global_install,
            )
        )
        hooks[event_name] = entries
    config["hooks"] = hooks
    write_json(config_path, config)
    enable_codex_hooks_feature(global_toml_config_path(home_dir) if global_install else repo_toml_config_path(repo_path))
    return config_path


def uninstall_codex_hooks(repo_path: Path, global_install: bool = False, home_dir: Path | None = None) -> Path:
    config_path = global_config_path(home_dir) if global_install else repo_config_path(repo_path)
    config = read_json(config_path, {})
    hooks = config.get("hooks", {})
    for event_name in list(hooks):
        hooks[event_name] = [entry for entry in hooks[event_name] if entry.get("agentium_integration") != "codex"]
        if not hooks[event_name]:
            hooks.pop(event_name)
    if hooks:
        config["hooks"] = hooks
    else:
        config.pop("hooks", None)
    write_json(config_path, config)
    return config_path


def codex_hook_status(repo_path: Path, global_install: bool = False, home_dir: Path | None = None) -> dict:
    config_path = global_config_path(home_dir) if global_install else repo_config_path(repo_path)
    config = read_json(config_path, {})
    hooks = config.get("hooks", {})
    installed_events = []
    for event_name in CODEX_HOOK_EVENTS:
        if any(entry.get("agentium_integration") == "codex" for entry in hooks.get(event_name, [])):
            installed_events.append(event_name)
    return {
        "integration": "codex",
        "scope": "global" if global_install else "repo",
        "config_path": str(config_path),
        "installed": set(installed_events) == set(CODEX_HOOK_EVENTS),
        "installed_events": installed_events,
        "missing_events": [event for event in CODEX_HOOK_EVENTS if event not in installed_events],
    }


@dataclass
class CodexHookResult:
    event_name: str
    task_id: str | None
    emitted_events: int
    skipped: bool = False
    reason: str | None = None


@dataclass
class CodexSessionCaptureResult:
    task_id: str
    trace_path: Path
    event_count: int
    uploaded: bool = False
    upload_response: dict | None = None


class CodexHookCollector:
    def __init__(
        self,
        repo_path: Path | str = ".",
        base_url: str = "http://localhost:8000/api",
        project_id: str | None = None,
        client: AgentRuntimeClient | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.base_url = base_url
        self.project_id = project_id or self.repo_path.name or "default"
        self.client = client or AgentRuntimeClient(base_url)
        self.state_file = state_path(self.repo_path)

    def load_state(self) -> dict:
        return read_json(self.state_file, {"sessions": {}, "turns": {}})

    def save_state(self, state: dict) -> None:
        write_json(self.state_file, state)

    def state_key(self, payload: dict) -> str:
        session_id = str(payload.get("session_id") or "unknown_session")
        turn_id = str(payload.get("turn_id") or payload.get("turnId") or "active_turn")
        return f"{session_id}:{turn_id}"

    def active_task_id(self, state: dict, payload: dict) -> str | None:
        key = self.state_key(payload)
        session_id = str(payload.get("session_id") or "unknown_session")
        turn = state.get("turns", {}).get(key)
        if turn:
            return turn.get("task_id")
        session = state.get("sessions", {}).get(session_id)
        return session.get("active_task_id") if session else None

    def create_turn_task(self, state: dict, payload: dict) -> str:
        key = self.state_key(payload)
        session_id = str(payload.get("session_id") or "unknown_session")
        goal = redact_text(prompt_text(payload))
        task_id = self.client.create_task(goal=goal, project_id=self.project_id, agent_type="codex")
        state.setdefault("turns", {})[key] = {
            "task_id": task_id,
            "task_span_id": f"span_task_{uuid4().hex[:8]}",
            "prompt": goal,
            "started_at": utc_now(),
        }
        state.setdefault("sessions", {}).setdefault(session_id, {})["active_task_id"] = task_id
        return task_id

    def task_span_id(self, state: dict, payload: dict) -> str:
        key = self.state_key(payload)
        return state.get("turns", {}).get(key, {}).get("task_span_id", f"span_task_{uuid4().hex[:8]}")

    def add_event(
        self,
        task_id: str,
        event_type: str,
        span_id: str,
        name: str,
        attributes: dict | None = None,
        payload: dict | None = None,
        parent_span_id: str | None = None,
    ) -> None:
        event = TraceEvent(
            task_id=task_id,
            event_type=event_type,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes=redact_value(attributes or {}),
            payload=redact_value(payload or {}),
        )
        self.client.add_event(event)

    def handle(self, event_name: str, payload: dict) -> CodexHookResult:
        state = self.load_state()
        emitted = 0
        try:
            if event_name == "SessionStart":
                session_id = str(payload.get("session_id") or "unknown_session")
                state.setdefault("sessions", {}).setdefault(session_id, {})["started_at"] = utc_now()
                state["sessions"][session_id]["cwd"] = payload.get("cwd")
                self.save_state(state)
                return CodexHookResult(event_name=event_name, task_id=None, emitted_events=0)

            if event_name == "UserPromptSubmit":
                task_id = self.create_turn_task(state, payload)
                task_span_id = self.task_span_id(state, payload)
                self.add_event(
                    task_id,
                    "task_start",
                    task_span_id,
                    "codex_turn_start",
                    attributes={
                        "integration": "codex",
                        "session_id": payload.get("session_id"),
                        "turn_id": payload.get("turn_id") or payload.get("turnId"),
                        "cwd": payload.get("cwd"),
                        "model": payload.get("model"),
                    },
                    payload={"goal": redact_text(prompt_text(payload)), "agent_type": "codex"},
                )
                self.add_event(
                    task_id,
                    "context_snapshot",
                    f"span_context_{uuid4().hex[:8]}",
                    "codex_user_prompt",
                    attributes={
                        "context_kind": "user_prompt",
                        "source": "codex_hook",
                        "size_tokens": max(1, len(prompt_text(payload).split())),
                    },
                    payload={"prompt_preview": compact_preview(redact_text(prompt_text(payload)))},
                    parent_span_id=task_span_id,
                )
                emitted = 2
                self.save_state(state)
                return CodexHookResult(event_name=event_name, task_id=task_id, emitted_events=emitted)

            task_id = self.active_task_id(state, payload)
            if not task_id:
                return CodexHookResult(
                    event_name=event_name,
                    task_id=None,
                    emitted_events=0,
                    skipped=True,
                    reason="No active Codex task for hook event.",
                )
            task_span_id = self.task_span_id(state, payload)

            if event_name == "PreToolUse":
                tool_use_id = str(payload.get("tool_use_id") or payload.get("toolCallId") or uuid4().hex[:8])
                span_id = f"span_codex_tool_{tool_use_id[-8:]}"
                self.add_event(
                    task_id,
                    "tool_call_start",
                    span_id,
                    f"codex_{payload.get('tool_name', 'tool')}",
                    attributes={
                        "integration": "codex",
                        "tool_name": payload.get("tool_name"),
                        "tool_use_id": tool_use_id,
                        "cwd": payload.get("cwd"),
                    },
                    payload={"tool_input": compact_preview(redact_value(payload.get("tool_input", {})))},
                    parent_span_id=task_span_id,
                )
                return CodexHookResult(event_name=event_name, task_id=task_id, emitted_events=1)

            if event_name == "PostToolUse":
                tool_use_id = str(payload.get("tool_use_id") or payload.get("toolCallId") or uuid4().hex[:8])
                span_id = f"span_codex_tool_{tool_use_id[-8:]}"
                tool_name = str(payload.get("tool_name") or "tool")
                self.add_event(
                    task_id,
                    "tool_call_end",
                    span_id,
                    f"codex_{tool_name}_end",
                    attributes={
                        "integration": "codex",
                        "tool_name": tool_name,
                        "tool_use_id": tool_use_id,
                        "status": "success",
                        "latency_ms": int(payload.get("duration_ms", 0) or 0),
                    },
                    payload={"tool_response": compact_preview(redact_value(payload.get("tool_response", {})))},
                    parent_span_id=task_span_id,
                )
                emitted = 1
                if tool_name.lower() in {"bash", "terminal", "shell"}:
                    self.add_event(
                        task_id,
                        "terminal_event",
                        f"span_terminal_{uuid4().hex[:8]}",
                        "codex_terminal_output",
                        attributes={
                            "integration": "codex",
                            "command": (payload.get("tool_input") or {}).get("command")
                            if isinstance(payload.get("tool_input"), dict)
                            else None,
                            "duration_ms": int(payload.get("duration_ms", 0) or 0),
                        },
                        payload={"tool_response": compact_preview(redact_value(payload.get("tool_response", {})))},
                        parent_span_id=span_id,
                    )
                    emitted += 1
                if tool_name.lower() in {"edit", "write", "apply_patch"}:
                    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
                    self.add_event(
                        task_id,
                        "file_event",
                        f"span_file_{uuid4().hex[:8]}",
                        "codex_file_change",
                        attributes={
                            "integration": "codex",
                            "operation": "write" if tool_name.lower() in {"write", "edit"} else "diff",
                            "path": tool_input.get("file_path") or tool_input.get("path"),
                            "content_stored": False,
                        },
                        parent_span_id=span_id,
                    )
                    emitted += 1
                return CodexHookResult(event_name=event_name, task_id=task_id, emitted_events=emitted)

            if event_name == "Stop":
                self.add_event(
                    task_id,
                    "task_end",
                    task_span_id,
                    "codex_turn_end",
                    payload={
                        "status": "completed",
                        "summary": "Codex hook trace completed.",
                    },
                )
                return CodexHookResult(event_name=event_name, task_id=task_id, emitted_events=1)

            return CodexHookResult(event_name=event_name, task_id=task_id, emitted_events=0, skipped=True)
        except Exception as exc:
            return CodexHookResult(
                event_name=event_name,
                task_id=None,
                emitted_events=emitted,
                skipped=True,
                reason=str(exc),
            )


def run_codex_hook(event_name: str, repo_path: Path, base_url: str, project_id: str | None = None) -> CodexHookResult:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        return CodexHookResult(event_name=event_name, task_id=None, emitted_events=0, skipped=True, reason=str(exc))
    return CodexHookCollector(repo_path=repo_path, base_url=base_url, project_id=project_id).handle(event_name, payload)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def stable_hash(value: str, length: int = 12) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def extract_content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("input_text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def first_payload(records: list[dict[str, Any]], payload_type: str) -> dict[str, Any] | None:
    for record in records:
        payload = record.get("payload")
        if isinstance(payload, dict) and payload.get("type") == payload_type:
            return payload
    return None


def session_metadata(records: list[dict[str, Any]]) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if record.get("type") == "session_meta":
            for key in ("id", "cwd", "originator", "cli_version", "source", "model_provider"):
                if payload.get(key) is not None:
                    meta[key] = payload.get(key)
        if record.get("type") == "turn_context":
            for key in ("cwd", "model", "approval_policy", "personality"):
                if payload.get(key) is not None:
                    meta[key] = payload.get(key)
    return meta


def codex_goal(records: list[dict[str, Any]]) -> str:
    user_event = first_payload(records, "user_message")
    if user_event and isinstance(user_event.get("message"), str):
        return redact_text(user_event["message"])
    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("type") == "message" and payload.get("role") == "user":
            text = extract_content_text(payload.get("content"))
            if text.strip():
                return redact_text(text)
    return "Codex session"


def latest_token_usage(records: list[dict[str, Any]]) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "token_count":
            continue
        info = payload.get("info")
        if isinstance(info, dict):
            total = info.get("total_token_usage")
            last = info.get("last_token_usage")
            if isinstance(total, dict):
                latest = total
            elif isinstance(last, dict):
                latest = last
    return latest


def first_timestamp(records: list[dict[str, Any]]) -> str:
    for record in records:
        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            return timestamp
    return utc_now()


def last_timestamp(records: list[dict[str, Any]]) -> str:
    for record in reversed(records):
        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            return timestamp
    return utc_now()


def make_event(
    task_id: str,
    event_type: str,
    span_id: str,
    name: str,
    timestamp: str,
    attributes: dict | None = None,
    payload: dict | None = None,
    parent_span_id: str | None = None,
) -> dict[str, Any]:
    return TraceEvent(
        task_id=task_id,
        event_type=event_type,
        span_id=span_id,
        parent_span_id=parent_span_id,
        name=name,
        attributes=redact_value(attributes or {}),
        payload=redact_value(payload or {}),
        timestamp=timestamp,
    ).to_dict()


def parse_function_arguments(value: object) -> dict[str, Any]:
    if not isinstance(value, str):
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def parse_exit_code(output: object) -> int | None:
    if not isinstance(output, str):
        return None
    first_line = output.splitlines()[0] if output.splitlines() else ""
    if first_line.lower().startswith("exit code:"):
        try:
            return int(first_line.split(":", 1)[1].strip())
        except ValueError:
            return None
    return None


def extract_file_changes(payload: dict[str, Any]) -> list[tuple[str, str]]:
    changes = payload.get("changes")
    if not isinstance(changes, dict):
        return []
    extracted: list[tuple[str, str]] = []
    for path, change in changes.items():
        operation = "change"
        if isinstance(change, dict) and isinstance(change.get("type"), str):
            operation = change["type"]
        extracted.append((str(path), operation))
    return extracted


def convert_codex_session_jsonl_to_trace(
    session_file: Path,
    project_id: str = "default",
    task_id: str | None = None,
) -> dict[str, Any]:
    records = read_jsonl(session_file)
    meta = session_metadata(records)
    session_id = str(meta.get("id") or stable_hash(str(session_file.resolve())))
    task_id = task_id or f"task_codex_session_{stable_hash(session_id)}"
    task_span_id = f"span_task_{stable_hash(task_id, 8)}"
    goal = codex_goal(records)
    events: list[dict[str, Any]] = []
    tool_spans: dict[str, dict[str, Any]] = {}

    events.append(
        make_event(
            task_id,
            "task_start",
            task_span_id,
            "codex_session_start",
            first_timestamp(records),
            attributes={
                "integration": "codex",
                "capture_source": "codex_session_jsonl",
                "session_id": session_id,
                "cwd": meta.get("cwd"),
                "model": meta.get("model"),
                "cli_version": meta.get("cli_version"),
                "source": meta.get("source"),
                "model_provider": meta.get("model_provider"),
            },
            payload={"goal": goal, "agent_type": "codex"},
        )
    )

    events.append(
        make_event(
            task_id,
            "context_snapshot",
            f"span_context_{stable_hash(goal, 8)}",
            "codex_user_prompt",
            first_timestamp(records),
            attributes={
                "integration": "codex",
                "context_kind": "user_prompt",
                "source": "codex_session_jsonl",
                "size_tokens": max(1, len(goal.split())),
            },
            payload={"prompt_preview": compact_preview(goal)},
            parent_span_id=task_span_id,
        )
    )

    assistant_timestamps = [
        record.get("timestamp")
        for record in records
        if isinstance(record.get("payload"), dict)
        and record["payload"].get("type") in {"agent_message", "token_count"}
        and isinstance(record.get("timestamp"), str)
    ]
    token_usage = latest_token_usage(records)
    if assistant_timestamps or token_usage:
        model_span_id = f"span_codex_model_{stable_hash(session_id, 8)}"
        model_start = assistant_timestamps[0] if assistant_timestamps else first_timestamp(records)
        model_end = assistant_timestamps[-1] if assistant_timestamps else last_timestamp(records)
        events.append(
            make_event(
                task_id,
                "model_call_start",
                model_span_id,
                "codex_model_call",
                model_start,
                attributes={
                    "integration": "codex",
                    "capture_source": "codex_session_jsonl",
                    "model": meta.get("model"),
                    "provider": meta.get("model_provider"),
                    "measurement": "session_token_usage",
                },
                parent_span_id=task_span_id,
            )
        )
        input_tokens = int(token_usage.get("input_tokens") or 0)
        output_tokens = int(token_usage.get("output_tokens") or 0)
        cached_input_tokens = int(token_usage.get("cached_input_tokens") or 0)
        events.append(
            make_event(
                task_id,
                "model_call_end",
                model_span_id,
                "codex_model_call_end",
                model_end,
                attributes={
                    "integration": "codex",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_input_tokens": cached_input_tokens,
                    "total_tokens": int(token_usage.get("total_tokens") or input_tokens + output_tokens),
                    "cost_dollars": 0.0,
                    "status": "completed",
                },
                payload={"token_usage_source": "codex_session_jsonl"},
                parent_span_id=task_span_id,
            )
        )

    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        timestamp = record.get("timestamp") if isinstance(record.get("timestamp"), str) else utc_now()
        payload_type = payload.get("type")

        if payload_type == "custom_tool_call":
            call_id = str(payload.get("call_id") or uuid4().hex[:12])
            tool_name = str(payload.get("name") or "custom_tool")
            span_id = f"span_codex_tool_{stable_hash(call_id, 8)}"
            tool_spans[call_id] = {"span_id": span_id, "tool_name": tool_name}
            events.append(
                make_event(
                    task_id,
                    "tool_call_start",
                    span_id,
                    f"codex_{tool_name}",
                    timestamp,
                    attributes={
                        "integration": "codex",
                        "tool_name": tool_name,
                        "call_id": call_id,
                        "capture_source": "codex_session_jsonl",
                    },
                    payload={"input_preview": compact_preview(redact_text(str(payload.get("input") or "")))},
                    parent_span_id=task_span_id,
                )
            )

        if payload_type == "patch_apply_end":
            call_id = str(payload.get("call_id") or uuid4().hex[:12])
            span = tool_spans.get(call_id, {})
            span_id = str(span.get("span_id") or f"span_codex_tool_{stable_hash(call_id, 8)}")
            tool_spans.setdefault(call_id, {"span_id": span_id, "tool_name": "apply_patch"})
            events.append(
                make_event(
                    task_id,
                    "tool_call_end",
                    span_id,
                    "codex_apply_patch_end",
                    timestamp,
                    attributes={
                        "integration": "codex",
                        "tool_name": span.get("tool_name") or "apply_patch",
                        "call_id": call_id,
                        "status": "success" if payload.get("success") else "failed",
                    },
                    payload={
                        "stdout_preview": compact_preview(redact_text(str(payload.get("stdout") or ""))),
                        "stderr_preview": compact_preview(redact_text(str(payload.get("stderr") or ""))),
                    },
                    parent_span_id=task_span_id,
                )
            )
            for path, operation in extract_file_changes(payload):
                events.append(
                    make_event(
                        task_id,
                        "file_event",
                        f"span_file_{stable_hash(path + operation, 8)}",
                        "codex_file_change",
                        timestamp,
                        attributes={
                            "integration": "codex",
                            "operation": operation,
                            "path": path,
                            "content_stored": False,
                            "capture_source": "codex_session_jsonl",
                        },
                        parent_span_id=span_id,
                    )
                )

        if payload_type == "function_call":
            call_id = str(payload.get("call_id") or uuid4().hex[:12])
            tool_name = str(payload.get("name") or "function")
            span_id = f"span_codex_tool_{stable_hash(call_id, 8)}"
            arguments = parse_function_arguments(payload.get("arguments"))
            tool_spans[call_id] = {"span_id": span_id, "tool_name": tool_name, "arguments": arguments}
            events.append(
                make_event(
                    task_id,
                    "tool_call_start",
                    span_id,
                    f"codex_{tool_name}",
                    timestamp,
                    attributes={
                        "integration": "codex",
                        "tool_name": tool_name,
                        "call_id": call_id,
                        "command": arguments.get("command"),
                        "workdir": arguments.get("workdir"),
                        "capture_source": "codex_session_jsonl",
                    },
                    payload={"arguments_preview": compact_preview(redact_value(arguments))},
                    parent_span_id=task_span_id,
                )
            )

        if payload_type == "function_call_output":
            call_id = str(payload.get("call_id") or uuid4().hex[:12])
            span = tool_spans.get(call_id, {})
            span_id = str(span.get("span_id") or f"span_codex_tool_{stable_hash(call_id, 8)}")
            tool_name = str(span.get("tool_name") or "function")
            output = str(payload.get("output") or "")
            exit_code = parse_exit_code(output)
            events.append(
                make_event(
                    task_id,
                    "tool_call_end",
                    span_id,
                    f"codex_{tool_name}_end",
                    timestamp,
                    attributes={
                        "integration": "codex",
                        "tool_name": tool_name,
                        "call_id": call_id,
                        "status": "success" if exit_code in {None, 0} else "failed",
                        "exit_code": exit_code,
                    },
                    payload={"output_preview": compact_preview(redact_text(output))},
                    parent_span_id=task_span_id,
                )
            )
            if tool_name == "shell_command":
                arguments = span.get("arguments") if isinstance(span.get("arguments"), dict) else {}
                events.append(
                    make_event(
                        task_id,
                        "terminal_event",
                        f"span_terminal_{stable_hash(call_id, 8)}",
                        "codex_terminal_output",
                        timestamp,
                        attributes={
                            "integration": "codex",
                            "command": arguments.get("command"),
                            "workdir": arguments.get("workdir"),
                            "exit_code": exit_code,
                            "capture_source": "codex_session_jsonl",
                        },
                        payload={"output_preview": compact_preview(redact_text(output))},
                        parent_span_id=span_id,
                    )
                )

    task_complete = first_payload(records, "task_complete")
    success = task_complete is not None
    duration_ms = task_complete.get("duration_ms") if task_complete else None
    changed_files = {
        event["attributes"].get("path")
        for event in events
        if event["event_type"] == "file_event" and event.get("attributes", {}).get("path")
    }
    summary_text = ""
    if isinstance(task_complete, dict):
        summary_text = strip_markdown_links(str(task_complete.get("last_agent_message") or ""))
    events.append(
        make_event(
            task_id,
            "task_end",
            task_span_id,
            "codex_session_end",
            task_complete.get("completed_at") if isinstance(task_complete, dict) and isinstance(task_complete.get("completed_at"), str) else last_timestamp(records),
            attributes={
                "integration": "codex",
                "capture_source": "codex_session_jsonl",
                "duration_ms": duration_ms,
            },
            payload={
                "status": "completed" if success else "unknown",
                "summary": compact_preview(redact_text(summary_text)) if summary_text else "Codex session JSONL imported.",
            },
        )
    )

    return {
        "project_id": project_id,
        "task": {
            "project_id": project_id,
            "task_id": task_id,
            "goal": goal,
            "agent_type": "codex",
            "agent_name": "codex",
            "repo_name": Path(str(meta.get("cwd") or "")).name if meta.get("cwd") else None,
            "task_success": success,
            "patch_generated": bool(changed_files),
            "files_changed_count": len(changed_files),
        },
        "events": events,
    }


def capture_codex_session_jsonl(
    session_file: Path,
    project_id: str = "default",
    trace_dir: Path = Path(".agent-runtime") / "traces",
    upload: bool = False,
    base_url: str = "http://localhost:8000/api",
) -> CodexSessionCaptureResult:
    trace = convert_codex_session_jsonl_to_trace(session_file=session_file, project_id=project_id)
    task_id = trace["task"]["task_id"]
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{task_id}.json"
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    upload_response = None
    if upload:
        upload_response = AgentRuntimeClient(base_url).import_trace_file(trace_path)
    return CodexSessionCaptureResult(
        task_id=task_id,
        trace_path=trace_path,
        event_count=len(trace["events"]),
        uploaded=upload,
        upload_response=upload_response,
    )
