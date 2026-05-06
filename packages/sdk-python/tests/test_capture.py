import json
import sys
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer.capture import capture_command


def trace_dir():
    path = Path("test-artifacts") / uuid4().hex / "traces"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_trace(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_successful_command_creates_trace_json():
    result = capture_command(
        name="hello test",
        command=[sys.executable, "-c", "print('hello')"],
        trace_dir=trace_dir(),
    )

    trace = load_trace(result.trace_path)
    assert result.exit_code == 0
    assert trace["task"]["task_id"] == result.task_id
    assert [event["event_type"] for event in trace["events"]] == [
        "task_start",
        "tool_call_start",
        "terminal_event",
        "tool_call_end",
        "task_end",
    ]
    terminal = next(event for event in trace["events"] if event["event_type"] == "terminal_event")
    assert terminal["attributes"]["exit_code"] == 0
    assert "hello" in terminal["attributes"]["stdout_preview"]
    assert trace["events"][-1]["payload"]["status"] == "completed"


def test_failing_command_creates_failed_trace_json():
    result = capture_command(
        name="failure test",
        command=[sys.executable, "-c", "import sys; print('bad'); sys.exit(7)"],
        trace_dir=trace_dir(),
    )

    trace = load_trace(result.trace_path)
    tool_end = next(event for event in trace["events"] if event["event_type"] == "tool_call_end")
    assert result.exit_code == 7
    assert tool_end["attributes"]["status"] == "failed"
    assert tool_end["attributes"]["exit_code"] == 7
    assert trace["events"][-1]["payload"]["status"] == "failed"


def test_stdout_and_stderr_are_redacted():
    result = capture_command(
        name="secret redaction",
        command=[
            sys.executable,
            "-c",
            "import sys; print('api_key=abc123 sk-testsecret999'); print('password=hunter2', file=sys.stderr)",
        ],
        trace_dir=trace_dir(),
        capture_full_logs=True,
    )

    trace_text = result.trace_path.read_text(encoding="utf-8")
    assert "abc123" not in trace_text
    assert "sk-testsecret999" not in trace_text
    assert "hunter2" not in trace_text
    assert "[REDACTED]" in trace_text
