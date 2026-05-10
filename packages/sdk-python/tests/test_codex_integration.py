import json
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.integrations.codex import (
    CODEX_HOOK_EVENTS,
    CodexHookCollector,
    capture_codex_session_jsonl,
    codex_hook_status,
    convert_codex_session_jsonl_to_trace,
    install_codex_hooks,
    uninstall_codex_hooks,
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


def test_install_status_and_uninstall_codex_hooks():
    repo = artifact_dir()
    config_path = install_codex_hooks(repo, base_url="http://localhost:8000/api", project_id="demo")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert set(config["hooks"]) == set(CODEX_HOOK_EVENTS)
    assert codex_hook_status(repo)["installed"] is True
    toml_config = (repo / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "hooks = true" in toml_config
    for event_name in CODEX_HOOK_EVENTS:
        command = config["hooks"][event_name][0]["hooks"][0]["command"]
        assert "agent-runtime --base-url http://localhost:8000/api codex-hook" in command
        assert f"--event {event_name}" in command

    uninstall_codex_hooks(repo)
    status = codex_hook_status(repo)
    assert status["installed"] is False
    assert status["installed_events"] == []


def test_global_install_status_and_uninstall_codex_hooks():
    home = artifact_dir()
    repo = artifact_dir()
    config_path = install_codex_hooks(
        repo,
        base_url="http://localhost:8000/api",
        project_id="demo",
        global_install=True,
        home_dir=home,
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config_path == home / ".codex" / "hooks.json"
    assert set(config["hooks"]) == set(CODEX_HOOK_EVENTS)
    for event_name in CODEX_HOOK_EVENTS:
        command = config["hooks"][event_name][0]["hooks"][0]["command"]
        assert "agent-runtime --base-url http://localhost:8000/api codex-hook" in command
        assert f"--event {event_name}" in command
    toml_config = (home / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "hooks = true" in toml_config
    status = codex_hook_status(repo, global_install=True, home_dir=home)
    assert status["installed"] is True
    assert status["scope"] == "global"

    uninstall_codex_hooks(repo, global_install=True, home_dir=home)
    status = codex_hook_status(repo, global_install=True, home_dir=home)
    assert status["installed"] is False


def test_global_install_uses_source_tree_launcher_when_available():
    import sys
    home = artifact_dir()
    # repo root is two levels above the sdk-python package directory
    repo = Path(__file__).resolve().parent.parent.parent.parent
    config_path = install_codex_hooks(
        repo,
        base_url="http://localhost:8000/api",
        project_id="demo",
        global_install=True,
        home_dir=home,
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    command = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "packages/sdk-python" in command or "packages\\sdk-python" in command
    assert "-m agent_runtime_layer.cli" in command
    assert "codex-hook" in command
    if sys.platform == "win32":
        assert "powershell.exe" in command
        assert "--event 'UserPromptSubmit'" in command
    else:
        assert "PYTHONPATH=" in command
        assert "--event UserPromptSubmit" in command


def test_codex_hook_sequence_creates_trace_events():
    repo = artifact_dir()
    client = FakeClient()
    collector = CodexHookCollector(repo_path=repo, project_id="demo", client=client)
    base_payload = {
        "session_id": "session_123",
        "turn_id": "turn_001",
        "cwd": str(repo),
        "model": "gpt-5-codex",
    }

    collector.handle("SessionStart", base_payload)
    collector.handle("UserPromptSubmit", {**base_payload, "prompt": "Fix failing tests"})
    collector.handle(
        "PreToolUse",
        {
            **base_payload,
            "tool_name": "Bash",
            "tool_use_id": "toolu_12345678",
            "tool_input": {"command": "pytest tests"},
        },
    )
    collector.handle(
        "PostToolUse",
        {
            **base_payload,
            "tool_name": "Bash",
            "tool_use_id": "toolu_12345678",
            "duration_ms": 42,
            "tool_input": {"command": "pytest tests"},
            "tool_response": {"stdout": "2 passed", "stderr": ""},
        },
    )
    collector.handle("Stop", base_payload)

    assert client.created == [
        {"task_id": "task_fake_1", "goal": "Fix failing tests", "project_id": "demo", "agent_type": "codex"}
    ]
    event_types = [event["event_type"] for event in client.events]
    assert event_types == [
        "task_start",
        "context_snapshot",
        "tool_call_start",
        "tool_call_end",
        "terminal_event",
        "task_end",
    ]
    assert client.events[0]["attributes"]["integration"] == "codex"
    assert client.events[2]["attributes"]["tool_name"] == "Bash"
    assert client.events[4]["attributes"]["command"] == "pytest tests"


def test_codex_hook_file_tool_adds_file_event():
    repo = artifact_dir()
    client = FakeClient()
    collector = CodexHookCollector(repo_path=repo, project_id="demo", client=client)
    base_payload = {"session_id": "session_123", "turn_id": "turn_001", "cwd": str(repo)}

    collector.handle("UserPromptSubmit", {**base_payload, "prompt": "Edit app.py"})
    collector.handle(
        "PostToolUse",
        {
            **base_payload,
            "tool_name": "Write",
            "tool_use_id": "toolu_file1234",
            "tool_input": {"file_path": "app.py", "content": "secret sk-testsecret999"},
            "tool_response": {"success": True},
        },
    )

    file_event = next(event for event in client.events if event["event_type"] == "file_event")
    assert file_event["attributes"]["integration"] == "codex"
    assert file_event["attributes"]["path"] == "app.py"
    trace_text = json.dumps(client.events)
    assert "sk-testsecret999" not in trace_text


def test_convert_codex_session_jsonl_to_trace_captures_real_session_shape():
    repo = artifact_dir()
    session_file = repo / "rollout.jsonl"
    changed_path = repo / "hello-codex.txt"
    records = [
        {
            "timestamp": "2026-05-08T04:31:31.266Z",
            "type": "session_meta",
            "payload": {
                "id": "019e05da-d08e-7d31-a322-ed0b2eea0960",
                "cwd": str(repo),
                "cli_version": "0.129.0",
                "source": "exec",
                "model_provider": "openai",
            },
        },
        {
            "timestamp": "2026-05-08T04:31:31.269Z",
            "type": "turn_context",
            "payload": {"cwd": str(repo), "model": "gpt-5.5", "approval_policy": "never"},
        },
        {
            "timestamp": "2026-05-08T04:31:31.269Z",
            "type": "event_msg",
            "payload": {
                "type": "user_message",
                "message": "Create hello-codex.txt with token=sk-testsecret999",
            },
        },
        {
            "timestamp": "2026-05-08T04:31:34.212Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "status": "completed",
                "call_id": "call_patch_001",
                "name": "apply_patch",
                "input": "*** Begin Patch\n*** Add File: hello-codex.txt\n+hello\n*** End Patch\n",
            },
        },
        {
            "timestamp": "2026-05-08T04:31:36.659Z",
            "type": "event_msg",
            "payload": {
                "type": "patch_apply_end",
                "call_id": "call_patch_001",
                "stdout": "Success",
                "stderr": "",
                "success": True,
                "changes": {str(changed_path): {"type": "add", "content": "hello\n"}},
            },
        },
        {
            "timestamp": "2026-05-08T04:31:39.826Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "shell_command",
                "arguments": json.dumps({"command": "Get-Content hello-codex.txt", "workdir": str(repo)}),
                "call_id": "call_shell_001",
            },
        },
        {
            "timestamp": "2026-05-08T04:31:41.634Z",
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "call_shell_001",
                "output": "Exit code: 0\nWall time: 1 seconds\nOutput:\nhello\n",
            },
        },
        {
            "timestamp": "2026-05-08T04:31:43.000Z",
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "total_token_usage": {
                        "input_tokens": 1234,
                        "cached_input_tokens": 100,
                        "output_tokens": 56,
                        "total_tokens": 1290,
                    }
                },
            },
        },
        {
            "timestamp": "2026-05-08T04:31:44.529Z",
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "duration_ms": 15410,
                "last_agent_message": "Created [hello-codex.txt](C:/tmp/hello-codex.txt).",
            },
        },
    ]
    session_file.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    trace = convert_codex_session_jsonl_to_trace(session_file, project_id="codex-live-smoke")

    assert trace["project_id"] == "codex-live-smoke"
    assert trace["task"]["agent_type"] == "codex"
    assert trace["task"]["task_success"] is True
    assert trace["task"]["patch_generated"] is True
    event_types = [event["event_type"] for event in trace["events"]]
    assert "task_start" in event_types
    assert "context_snapshot" in event_types
    assert "model_call_start" in event_types
    assert "model_call_end" in event_types
    assert "tool_call_start" in event_types
    assert "tool_call_end" in event_types
    assert "file_event" in event_types
    assert "terminal_event" in event_types
    assert "task_end" in event_types
    model_end = next(event for event in trace["events"] if event["event_type"] == "model_call_end")
    assert model_end["attributes"]["input_tokens"] == 1234
    terminal = next(event for event in trace["events"] if event["event_type"] == "terminal_event")
    assert terminal["attributes"]["exit_code"] == 0
    task_end = next(event for event in trace["events"] if event["event_type"] == "task_end")
    assert task_end["payload"]["summary"] == "Created hello-codex.txt."
    trace_text = json.dumps(trace)
    assert "sk-testsecret999" not in trace_text
    assert "[REDACTED]" in trace_text


def test_capture_codex_session_jsonl_writes_trace_file():
    repo = artifact_dir()
    trace_dir = repo / "traces"
    session_file = repo / "rollout.jsonl"
    session_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-05-08T04:31:31.266Z",
                        "type": "session_meta",
                        "payload": {"id": "session_write_test", "cwd": str(repo), "source": "exec"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-05-08T04:31:31.269Z",
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": "hello codex"},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = capture_codex_session_jsonl(session_file, project_id="demo", trace_dir=trace_dir)

    assert result.uploaded is False
    assert result.trace_path.exists()
    trace = json.loads(result.trace_path.read_text(encoding="utf-8"))
    assert trace["task"]["task_id"] == result.task_id
    assert result.event_count == len(trace["events"])
