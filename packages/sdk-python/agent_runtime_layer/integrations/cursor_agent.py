import json
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_text, redact_value
from agent_runtime_layer.trace import TraceEvent


CONFIG_PATH = Path(".agent-runtime") / "cursor.json"


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


def install_cursor_capture(repo_path: Path, project_id: str | None = None) -> Path:
    path = repo_path / CONFIG_PATH
    write_json(
        path,
        {
            "agentium_integration": "cursor",
            "project_id": project_id,
            "capture_command": "cursor-agent --print --output-format stream-json | agent-runtime cursor-stream",
        },
    )
    return path


def uninstall_cursor_capture(repo_path: Path) -> Path:
    path = repo_path / CONFIG_PATH
    if path.exists():
        path.unlink()
    return path


def cursor_capture_status(repo_path: Path) -> dict:
    path = repo_path / CONFIG_PATH
    return {
        "integration": "cursor",
        "config_path": str(path),
        "installed": path.exists(),
        "mode": "stream-json",
    }


def cursor_prompt(event: dict) -> str:
    message = event.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "\n".join(parts)
    return "Cursor Agent run"


def tool_name_and_body(event: dict) -> tuple[str, dict]:
    tool_call = event.get("tool_call") if isinstance(event.get("tool_call"), dict) else {}
    if not tool_call:
        return "tool", {}
    key = next(iter(tool_call))
    name = key.removesuffix("ToolCall")
    return name, tool_call[key] if isinstance(tool_call[key], dict) else {}


@dataclass
class CursorStreamResult:
    task_id: str | None
    emitted_events: int
    skipped: bool = False
    reason: str | None = None


class CursorStreamCollector:
    def __init__(
        self,
        repo_path: Path | str = ".",
        base_url: str = "http://localhost:8000/api",
        project_id: str | None = None,
        name: str | None = None,
        client: AgentRuntimeClient | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.project_id = project_id or self.repo_path.name or "default"
        self.name = name
        self.client = client or AgentRuntimeClient(base_url)
        self.task_id: str | None = None
        self.task_span_id = f"span_task_{uuid4().hex[:8]}"
        self.system_metadata: dict = {}

    def add_event(self, event_type: str, span_id: str, name: str, attributes=None, payload=None, parent_span_id=None) -> None:
        if not self.task_id:
            return
        self.client.add_event(
            TraceEvent(
                task_id=self.task_id,
                event_type=event_type,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                attributes=redact_value(attributes or {}),
                payload=redact_value(payload or {}),
            )
        )

    def ensure_task(self, goal: str) -> None:
        if self.task_id:
            return
        safe_goal = redact_text(self.name or goal or "Cursor Agent run")
        self.task_id = self.client.create_task(goal=safe_goal, project_id=self.project_id, agent_type="cursor")
        self.add_event(
            "task_start",
            self.task_span_id,
            "cursor_run_start",
            attributes={
                "integration": "cursor",
                "session_id": self.system_metadata.get("session_id"),
                "cwd": self.system_metadata.get("cwd"),
                "model": self.system_metadata.get("model"),
            },
            payload={"goal": safe_goal, "agent_type": "cursor"},
        )

    def handle_event(self, event: dict) -> int:
        event_type = event.get("type")
        if event_type == "system":
            self.system_metadata = {**self.system_metadata, **event}
            return 0
        if event_type == "user":
            prompt = redact_text(cursor_prompt(event))
            self.ensure_task(prompt)
            self.add_event(
                "context_snapshot",
                f"span_context_{uuid4().hex[:8]}",
                "cursor_user_prompt",
                attributes={"integration": "cursor", "context_kind": "user_prompt", "size_tokens": max(1, len(prompt.split()))},
                payload={"prompt_preview": prompt},
                parent_span_id=self.task_span_id,
            )
            return 2
        if event_type == "tool_call":
            self.ensure_task("Cursor Agent run")
            tool_name, body = tool_name_and_body(event)
            call_id = str(event.get("call_id") or uuid4().hex[:8])
            span_id = f"span_cursor_tool_{call_id[-8:]}"
            if event.get("subtype") == "started":
                self.add_event(
                    "tool_call_start",
                    span_id,
                    f"cursor_{tool_name}",
                    attributes={"integration": "cursor", "tool_name": tool_name, "tool_call_id": call_id},
                    payload={"tool_input": redact_value(body.get("args", {}))},
                    parent_span_id=self.task_span_id,
                )
                return 1
            self.add_event(
                "tool_call_end",
                span_id,
                f"cursor_{tool_name}_end",
                attributes={"integration": "cursor", "tool_name": tool_name, "tool_call_id": call_id, "status": "success"},
                payload={"tool_result": redact_value(body.get("result", {}))},
                parent_span_id=self.task_span_id,
            )
            emitted = 1
            if tool_name.lower() == "write":
                args = body.get("args", {}) if isinstance(body.get("args"), dict) else {}
                result = body.get("result", {}) if isinstance(body.get("result"), dict) else {}
                success = result.get("success", {}) if isinstance(result.get("success"), dict) else {}
                self.add_event(
                    "file_event",
                    f"span_file_{uuid4().hex[:8]}",
                    "cursor_file_change",
                    attributes={"integration": "cursor", "operation": "write", "path": success.get("path") or args.get("path"), "content_stored": False},
                    parent_span_id=span_id,
                )
                emitted += 1
            return emitted
        if event_type == "result":
            self.ensure_task("Cursor Agent run")
            status = "failed" if event.get("is_error") else "completed"
            self.add_event(
                "task_end",
                self.task_span_id,
                "cursor_run_end",
                attributes={"integration": "cursor", "duration_ms": event.get("duration_ms"), "duration_api_ms": event.get("duration_api_ms")},
                payload={"status": status, "summary": redact_text(str(event.get("result") or "Cursor Agent run completed."))},
            )
            return 1
        return 0

    def handle_lines(self, lines: list[str]) -> CursorStreamResult:
        emitted = 0
        try:
            for line in lines:
                if not line.strip():
                    continue
                emitted += self.handle_event(json.loads(line))
            return CursorStreamResult(task_id=self.task_id, emitted_events=emitted)
        except Exception as exc:
            return CursorStreamResult(task_id=self.task_id, emitted_events=emitted, skipped=True, reason=str(exc))


def run_cursor_stream(repo_path: Path, base_url: str, project_id: str | None = None, name: str | None = None) -> CursorStreamResult:
    return CursorStreamCollector(repo_path=repo_path, base_url=base_url, project_id=project_id, name=name).handle_lines(sys.stdin.read().splitlines())
