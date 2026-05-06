import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_text, redact_value


DEFAULT_TRACE_DIR = Path(".agent-runtime") / "traces"
SUMMARY_LIMIT = 4000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def summarize_stream(value: str, limit: int = SUMMARY_LIMIT) -> str:
    redacted = redact_text(value)
    if len(redacted) <= limit:
        return redacted
    omitted = len(redacted) - limit
    return f"{redacted[:limit]}\n...[truncated {omitted} chars]"


def command_display(command: list[str]) -> str:
    return " ".join(command)


def safe_git_diff_summary() -> str | None:
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "--no-ext-diff"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr or "").strip()
    return summarize_stream(output, 2000) if output else None


@dataclass
class TraceCaptureResult:
    task_id: str
    trace_path: Path
    exit_code: int
    uploaded: bool = False
    upload_response: dict | None = None


class LocalTraceCapture:
    def __init__(
        self,
        name: str,
        command: list[str],
        project_id: str = "default",
        trace_dir: Path = DEFAULT_TRACE_DIR,
        capture_full_logs: bool = False,
        capture_diff: bool = False,
    ) -> None:
        if not command:
            raise ValueError("A command is required after --")
        self.name = name
        self.command = command
        self.project_id = project_id
        self.trace_dir = trace_dir
        self.capture_full_logs = capture_full_logs
        self.capture_diff = capture_diff
        self.task_id = f"task_local_{uuid4().hex[:12]}"
        self.task_span_id = f"span_task_{uuid4().hex[:8]}"
        self.tool_span_id = f"span_tool_{uuid4().hex[:8]}"

    def event(
        self,
        event_type: str,
        span_id: str,
        name: str,
        attributes: dict | None = None,
        payload: dict | None = None,
        parent_span_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict:
        return {
            "event_id": f"evt_{uuid4().hex[:12]}",
            "task_id": self.task_id,
            "timestamp": timestamp or utc_now(),
            "event_type": event_type,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "name": name,
            "attributes": redact_value(attributes or {}),
            "payload": redact_value(payload or {}),
        }

    def run(self) -> tuple[dict, int]:
        started_at = utc_now()
        start_time = time.perf_counter()
        display = command_display(self.command)
        events = [
            self.event(
                "task_start",
                self.task_span_id,
                "task_start",
                payload={
                    "goal": self.name,
                    "agent_type": "local_command",
                    "latency_slo_seconds": None,
                },
                timestamp=started_at,
            ),
            self.event(
                "tool_call_start",
                self.tool_span_id,
                "local_command",
                attributes={
                    "tool_name": "terminal",
                    "command": display,
                    "risk_level": "user_provided",
                },
                parent_span_id=self.task_span_id,
                timestamp=started_at,
            ),
        ]

        completed = subprocess.run(
            self.command,
            capture_output=True,
            text=True,
            check=False,
        )
        ended_at = utc_now()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        status = "success" if completed.returncode == 0 else "failed"
        stdout_preview = summarize_stream(completed.stdout or "")
        stderr_preview = summarize_stream(completed.stderr or "")
        terminal_payload = {
            "stdout_preview": stdout_preview,
            "stderr_preview": stderr_preview,
        }
        if self.capture_full_logs:
            terminal_payload["stdout"] = redact_text(completed.stdout or "")
            terminal_payload["stderr"] = redact_text(completed.stderr or "")
        if self.capture_diff:
            diff_summary = safe_git_diff_summary()
            if diff_summary:
                terminal_payload["git_diff_summary"] = diff_summary

        events.extend(
            [
                self.event(
                    "terminal_event",
                    f"span_terminal_{uuid4().hex[:8]}",
                    "local_command_output",
                    attributes={
                        "command": display,
                        "duration_ms": duration_ms,
                        "exit_code": completed.returncode,
                        "stdout_preview": stdout_preview,
                        "stderr_preview": stderr_preview,
                    },
                    payload=terminal_payload,
                    parent_span_id=self.tool_span_id,
                    timestamp=ended_at,
                ),
                self.event(
                    "tool_call_end",
                    self.tool_span_id,
                    "local_command_end",
                    attributes={
                        "latency_ms": duration_ms,
                        "status": status,
                        "exit_code": completed.returncode,
                    },
                    parent_span_id=self.task_span_id,
                    timestamp=ended_at,
                ),
                self.event(
                    "task_end",
                    self.task_span_id,
                    "task_end",
                    payload={
                        "status": "completed" if completed.returncode == 0 else "failed",
                        "summary": f"Command exited with code {completed.returncode}.",
                    },
                    timestamp=ended_at,
                ),
            ]
        )

        trace = {
            "project_id": self.project_id,
            "task": {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "goal": self.name,
                "agent_type": "local_command",
                "budget_dollars": None,
                "latency_slo_seconds": None,
            },
            "events": events,
        }
        return trace, completed.returncode

    def write(self, trace: dict) -> Path:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = self.trace_dir / f"{self.task_id}.json"
        trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
        return trace_path


def capture_command(
    name: str,
    command: list[str],
    project_id: str = "default",
    trace_dir: Path = DEFAULT_TRACE_DIR,
    capture_full_logs: bool = False,
    capture_diff: bool = False,
    upload: bool = False,
    base_url: str = "http://localhost:8000/api",
) -> TraceCaptureResult:
    capture = LocalTraceCapture(
        name=name,
        command=command,
        project_id=project_id,
        trace_dir=trace_dir,
        capture_full_logs=capture_full_logs,
        capture_diff=capture_diff,
    )
    trace, exit_code = capture.run()
    trace_path = capture.write(trace)
    upload_response = None
    if upload:
        upload_response = AgentRuntimeClient(base_url).import_trace_file(trace_path)
    return TraceCaptureResult(
        task_id=capture.task_id,
        trace_path=trace_path,
        exit_code=exit_code,
        uploaded=upload,
        upload_response=upload_response,
    )
