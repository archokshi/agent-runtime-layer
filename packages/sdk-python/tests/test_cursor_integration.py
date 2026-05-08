import json
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.integrations.cursor_agent import (
    CursorStreamCollector,
    cursor_capture_status,
    install_cursor_capture,
    uninstall_cursor_capture,
)


class FakeClient:
    def __init__(self) -> None:
        self.created = []
        self.events = []

    def create_task(self, goal: str, project_id: str = "default", agent_type: str = "coding_agent") -> str:
        task_id = f"task_fake_{len(self.created) + 1}"
        self.created.append({"task_id": task_id, "goal": goal, "project_id": project_id, "agent_type": agent_type})
        return task_id

    def add_event(self, event) -> dict:
        self.events.append(event.to_dict())
        return event.to_dict()


def artifact_dir() -> Path:
    path = Path("test-artifacts") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_install_status_and_uninstall_cursor_capture():
    repo = artifact_dir()
    config_path = install_cursor_capture(repo, project_id="demo")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["agentium_integration"] == "cursor"
    assert "cursor-agent --print --output-format stream-json" in config["capture_command"]
    assert cursor_capture_status(repo)["installed"] is True

    uninstall_cursor_capture(repo)
    assert cursor_capture_status(repo)["installed"] is False


def test_cursor_stream_creates_trace_events():
    repo = artifact_dir()
    client = FakeClient()
    collector = CursorStreamCollector(repo_path=repo, project_id="demo", client=client)
    lines = [
        json.dumps({"type": "system", "subtype": "init", "cwd": str(repo), "session_id": "session_123", "model": "Claude 4 Sonnet"}),
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Create summary"}]}, "session_id": "session_123"}),
        json.dumps({"type": "tool_call", "subtype": "started", "call_id": "toolu_read1234", "tool_call": {"readToolCall": {"args": {"path": "README.md"}}}, "session_id": "session_123"}),
        json.dumps({"type": "tool_call", "subtype": "completed", "call_id": "toolu_read1234", "tool_call": {"readToolCall": {"args": {"path": "README.md"}, "result": {"success": {"totalLines": 12}}}}, "session_id": "session_123"}),
        json.dumps({"type": "tool_call", "subtype": "completed", "call_id": "toolu_write1234", "tool_call": {"writeToolCall": {"args": {"path": "summary.md", "fileText": "secret sk-testsecret999"}, "result": {"success": {"path": "summary.md"}}}}, "session_id": "session_123"}),
        json.dumps({"type": "result", "subtype": "success", "duration_ms": 100, "duration_api_ms": 90, "is_error": False, "result": "done", "session_id": "session_123"}),
    ]

    result = collector.handle_lines(lines)
    event_types = [event["event_type"] for event in client.events]

    assert result.task_id == "task_fake_1"
    assert client.created == [{"task_id": "task_fake_1", "goal": "Create summary", "project_id": "demo", "agent_type": "cursor"}]
    assert event_types == [
        "task_start",
        "context_snapshot",
        "tool_call_start",
        "tool_call_end",
        "tool_call_end",
        "file_event",
        "task_end",
    ]
    file_event = next(event for event in client.events if event["event_type"] == "file_event")
    assert file_event["attributes"]["integration"] == "cursor"
    assert file_event["attributes"]["path"] == "summary.md"
    assert "sk-testsecret999" not in json.dumps(client.events)
