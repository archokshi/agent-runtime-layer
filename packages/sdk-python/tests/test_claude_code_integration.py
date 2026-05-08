import json
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.integrations.claude_code import (
    CLAUDE_HOOK_EVENTS,
    ClaudeHookCollector,
    claude_hook_status,
    install_claude_hooks,
    uninstall_claude_hooks,
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


def test_install_status_and_uninstall_claude_hooks():
    repo = artifact_dir()
    config_path = install_claude_hooks(repo, base_url="http://localhost:8000/api", project_id="demo")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert set(config["hooks"]) == set(CLAUDE_HOOK_EVENTS)
    assert claude_hook_status(repo)["installed"] is True
    assert config["hooks"]["PreToolUse"][0]["matcher"] == "*"
    assert "agent-runtime --base-url http://localhost:8000/api claude-hook --event PreToolUse" in config["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    uninstall_claude_hooks(repo)
    status = claude_hook_status(repo)
    assert status["installed"] is False
    assert status["installed_events"] == []


def test_claude_hook_sequence_creates_terminal_and_file_events():
    repo = artifact_dir()
    client = FakeClient()
    collector = ClaudeHookCollector(repo_path=repo, project_id="demo", client=client)
    base_payload = {"session_id": "session_123", "cwd": str(repo), "transcript_path": "transcript.jsonl"}

    collector.handle("SessionStart", base_payload)
    collector.handle("UserPromptSubmit", {**base_payload, "prompt": "Fix tests"})
    collector.handle("PreToolUse", {**base_payload, "tool_name": "Bash", "tool_use_id": "toolu_12345678", "tool_input": {"command": "pytest"}})
    collector.handle("PostToolUse", {**base_payload, "tool_name": "Bash", "tool_use_id": "toolu_12345678", "duration_ms": 50, "tool_input": {"command": "pytest"}, "tool_response": {"stdout": "passed"}})
    collector.handle("PostToolUse", {**base_payload, "tool_name": "Write", "tool_use_id": "toolu_file1234", "tool_input": {"file_path": "app.py", "content": "secret sk-testsecret999"}, "tool_response": {"success": True}})
    collector.handle("Stop", base_payload)

    assert client.created == [{"task_id": "task_fake_1", "goal": "Fix tests", "project_id": "demo", "agent_type": "claude-code"}]
    event_types = [event["event_type"] for event in client.events]
    assert "task_start" in event_types
    assert "context_snapshot" in event_types
    assert "terminal_event" in event_types
    assert "file_event" in event_types
    assert event_types[-1] == "task_end"
    assert "sk-testsecret999" not in json.dumps(client.events)


def test_claude_failed_tool_adds_error_event():
    repo = artifact_dir()
    client = FakeClient()
    collector = ClaudeHookCollector(repo_path=repo, project_id="demo", client=client)
    base_payload = {"session_id": "session_123", "cwd": str(repo)}

    collector.handle("UserPromptSubmit", {**base_payload, "prompt": "Run failing command"})
    collector.handle("PostToolUseFailure", {**base_payload, "tool_name": "Bash", "tool_use_id": "toolu_fail1234", "error": {"message": "boom"}})

    error = next(event for event in client.events if event["event_type"] == "error_event")
    assert error["attributes"]["integration"] == "claude-code"
    assert error["attributes"]["tool_name"] == "Bash"
