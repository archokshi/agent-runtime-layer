import json
import hashlib
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.capture import DEFAULT_TRACE_DIR, summarize_stream
from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_text, redact_value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def display_command(command: list[str]) -> str:
    return " ".join(command)


def output_indicates_failure(stdout: str, stderr: str) -> bool:
    combined = f"{stdout}\n{stderr}".lower()
    failure_markers = [
        "authenticationerror",
        "api_key",
        "not set",
        "the api provider is not able to authenticate",
        "traceback",
        "error:",
    ]
    return any(marker in combined for marker in failure_markers)


def parse_aider_model_metadata(stdout: str, stderr: str = "") -> dict | None:
    combined = f"{stdout}\n{stderr}"
    model_match = re.search(r"^Model:\s+([^\s]+)", combined, re.MULTILINE)
    token_match = re.search(
        r"Tokens:\s+([\d,.]+k?)\s+sent,\s+([\d,.]+k?)\s+received\.\s+Cost:\s+\$([0-9.]+)\s+message",
        combined,
        re.IGNORECASE,
    )
    if not model_match and not token_match:
        return None
    input_tokens = parse_token_count(token_match.group(1)) if token_match else 0
    output_tokens = parse_token_count(token_match.group(2)) if token_match else 0
    cost_dollars = float(token_match.group(3)) if token_match else 0.0
    return {
        "model": model_match.group(1) if model_match else "unknown",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_dollars": cost_dollars,
    }


def parse_token_count(value: str) -> int:
    normalized = value.lower().replace(",", "").strip()
    if normalized.endswith("k"):
        return int(float(normalized[:-1]) * 1000)
    return int(float(normalized))


def git_changed_files(repo_path: Path) -> list[dict]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    files = []
    for raw_line in result.stdout.splitlines():
        if not raw_line.strip():
            continue
        status = raw_line[:2].strip() or "modified"
        path_text = raw_line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        path = repo_path / path_text
        files.append(
            {
                "operation": "write" if status != "D" else "diff",
                "path": path_text.replace("\\", "/"),
                "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                "content_stored": False,
                "git_status": status,
            }
        )
    return files


def should_snapshot_file(path: Path, repo_path: Path) -> bool:
    try:
        relative = path.relative_to(repo_path)
    except ValueError:
        return False
    parts = set(relative.parts)
    if ".git" in parts or "__pycache__" in parts or ".agent-runtime" in parts:
        return False
    if any(part.startswith(".aider") for part in relative.parts):
        return False
    return path.is_file()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_snapshot(repo_path: Path) -> dict[str, dict]:
    snapshot = {}
    if not repo_path.exists():
        return snapshot
    for path in repo_path.rglob("*"):
        if not should_snapshot_file(path, repo_path):
            continue
        relative = path.relative_to(repo_path).as_posix()
        try:
            stat = path.stat()
            snapshot[relative] = {
                "bytes": stat.st_size,
                "digest": file_digest(path),
            }
        except OSError:
            continue
    return snapshot


def snapshot_changed_files(before: dict[str, dict], after: dict[str, dict]) -> list[dict]:
    changed = []
    for relative in sorted(set(before) | set(after)):
        before_info = before.get(relative)
        after_info = after.get(relative)
        if before_info == after_info:
            continue
        if before_info is None:
            operation = "create"
        elif after_info is None:
            operation = "delete"
        else:
            operation = "write"
        changed.append(
            {
                "operation": operation,
                "path": relative,
                "bytes": after_info["bytes"] if after_info else 0,
                "content_stored": False,
                "change_source": "snapshot",
            }
        )
    return changed


def merge_file_changes(git_files: list[dict], snapshot_files: list[dict]) -> list[dict]:
    merged = {file_info["path"]: file_info for file_info in snapshot_files}
    for file_info in git_files:
        merged[file_info["path"]] = {**merged.get(file_info["path"], {}), **file_info}
    return list(merged.values())


def snapshot_diff_summary(changed_files: list[dict]) -> str | None:
    if not changed_files:
        return None
    lines = []
    for file_info in changed_files:
        marker = {
            "create": "created",
            "delete": "deleted",
            "write": "modified",
            "diff": "changed",
        }.get(file_info["operation"], "changed")
        lines.append(f"{file_info['path']} | {marker}, {file_info.get('bytes', 0)} bytes")
    return summarize_stream("\n".join(lines), 2000)


@dataclass
class AiderIntegrationResult:
    task_id: str
    trace_path: Path
    exit_code: int
    uploaded: bool = False
    upload_response: dict | None = None


class AiderIntegrationCapture:
    def __init__(
        self,
        name: str,
        command: list[str],
        project_id: str = "default",
        repo_path: Path | str = ".",
        trace_dir: Path | str = DEFAULT_TRACE_DIR,
        capture_full_logs: bool = False,
    ) -> None:
        if not command:
            command = ["aider"]
        self.name = name
        self.command = command
        self.project_id = project_id
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.trace_dir = Path(trace_dir)
        self.capture_full_logs = capture_full_logs
        self.task_id = f"task_aider_{uuid4().hex[:12]}"
        self.task_span_id = f"span_task_{uuid4().hex[:8]}"
        self.aider_span_id = f"span_aider_{uuid4().hex[:8]}"

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
        command_text = display_command(self.command)
        events = [
            self.event(
                "task_start",
                self.task_span_id,
                "task_start",
                payload={
                    "goal": self.name,
                    "agent_type": "aider",
                },
                timestamp=started_at,
            ),
            self.event(
                "tool_call_start",
                self.aider_span_id,
                "aider_cli",
                attributes={
                    "tool_name": "aider",
                    "command": command_text,
                    "risk_level": "coding_agent",
                    "integration": "aider",
                    "adapter_version": "0.4.1",
                    "repo_path": str(self.repo_path),
                },
                parent_span_id=self.task_span_id,
                timestamp=started_at,
            ),
        ]
        before_snapshot = repo_snapshot(self.repo_path)
        completed = subprocess.run(
            self.command,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        ended_at = utc_now()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        stdout_preview = summarize_stream(completed.stdout or "")
        stderr_preview = summarize_stream(completed.stderr or "")
        model_metadata = parse_aider_model_metadata(completed.stdout or "", completed.stderr or "")
        after_snapshot = repo_snapshot(self.repo_path)
        snapshot_files = snapshot_changed_files(before_snapshot, after_snapshot)
        git_files = git_changed_files(self.repo_path)
        changed_files = merge_file_changes(git_files, snapshot_files)
        diff_summary = safe_git_diff_summary_for_repo(self.repo_path) or snapshot_diff_summary(changed_files)
        terminal_payload = {
            "stdout_preview": stdout_preview,
            "stderr_preview": stderr_preview,
            "git_diff_summary": diff_summary,
        }
        if self.capture_full_logs:
            terminal_payload["stdout"] = redact_text(completed.stdout or "")
            terminal_payload["stderr"] = redact_text(completed.stderr or "")
        events.append(
            self.event(
                "terminal_event",
                f"span_terminal_{uuid4().hex[:8]}",
                "aider_cli_output",
                attributes={
                    "command": command_text,
                    "duration_ms": duration_ms,
                    "exit_code": completed.returncode,
                    "stdout_preview": stdout_preview,
                    "stderr_preview": stderr_preview,
                },
                payload=terminal_payload,
                parent_span_id=self.aider_span_id,
                timestamp=ended_at,
            )
        )
        if model_metadata:
            model_span_id = f"span_model_{uuid4().hex[:8]}"
            events.extend(
                [
                    self.event(
                        "model_call_start",
                        model_span_id,
                        "aider_model_call",
                        attributes={
                            "model": model_metadata["model"],
                            "role": "coding_agent",
                            "estimated_input_tokens": model_metadata["input_tokens"],
                            "expected_output_tokens": model_metadata["output_tokens"],
                            "source": "aider_stdout",
                        },
                        parent_span_id=self.aider_span_id,
                        timestamp=started_at,
                    ),
                    self.event(
                        "model_call_end",
                        model_span_id,
                        "aider_model_call_end",
                        attributes={
                            "input_tokens": model_metadata["input_tokens"],
                            "output_tokens": model_metadata["output_tokens"],
                            "latency_ms": 0,
                            "cost_dollars": model_metadata["cost_dollars"],
                            "status": "success" if completed.returncode == 0 else "failed",
                            "source": "aider_stdout",
                        },
                        parent_span_id=self.aider_span_id,
                        timestamp=ended_at,
                    ),
                ]
            )
        for file_info in changed_files:
            events.append(
                self.event(
                    "file_event",
                    f"span_file_{uuid4().hex[:8]}",
                    "aider_file_change",
                    attributes=file_info,
                    parent_span_id=self.aider_span_id,
                    timestamp=ended_at,
                )
            )
        status = "success" if completed.returncode == 0 and not output_indicates_failure(completed.stdout or "", completed.stderr or "") else "failed"
        events.extend(
            [
                self.event(
                    "tool_call_end",
                    self.aider_span_id,
                    "aider_cli_end",
                    attributes={
                        "latency_ms": duration_ms,
                        "status": status,
                        "exit_code": completed.returncode,
                        "integration": "aider",
                    },
                    parent_span_id=self.task_span_id,
                    timestamp=ended_at,
                ),
                self.event(
                    "task_end",
                    self.task_span_id,
                    "task_end",
                    payload={
                        "status": "completed" if status == "success" else "failed",
                        "summary": f"Aider integration command exited with code {completed.returncode}.",
                    },
                    timestamp=ended_at,
                ),
            ]
        )
        return {
            "project_id": self.project_id,
            "task": {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "goal": self.name,
                "agent_type": "aider",
                "budget_dollars": None,
                "latency_slo_seconds": None,
            },
            "events": events,
        }, completed.returncode

    def write(self, trace: dict) -> Path:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = self.trace_dir / f"{self.task_id}.json"
        trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
        return trace_path


def safe_git_diff_summary_for_repo(repo_path: Path) -> str | None:
    repo_path = repo_path.expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "diff", "--stat", "--no-ext-diff"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return summarize_stream(f"Unable to collect git diff summary: {exc}", 2000)
    if result.returncode != 0:
        return None
    output = (result.stdout or result.stderr or "").strip()
    if "not a git repository" in output.lower():
        return None
    return summarize_stream(output, 2000) if output else None


def capture_aider(
    name: str,
    command: list[str] | None = None,
    project_id: str = "default",
    repo_path: Path | str = ".",
    trace_dir: Path | str = DEFAULT_TRACE_DIR,
    capture_full_logs: bool = False,
    upload: bool = False,
    base_url: str = "http://localhost:8000/api",
) -> AiderIntegrationResult:
    capture = AiderIntegrationCapture(
        name=name,
        command=command or ["aider"],
        project_id=project_id,
        repo_path=repo_path,
        trace_dir=trace_dir,
        capture_full_logs=capture_full_logs,
    )
    trace, exit_code = capture.run()
    trace_path = capture.write(trace)
    upload_response = None
    if upload:
        upload_response = AgentRuntimeClient(base_url).import_trace_file(trace_path)
    return AiderIntegrationResult(
        task_id=capture.task_id,
        trace_path=trace_path,
        exit_code=exit_code,
        uploaded=upload,
        upload_response=upload_response,
    )
