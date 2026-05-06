import json
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from agent_runtime_layer.integrations.aider import capture_aider, parse_aider_model_metadata


def artifact_dir() -> Path:
    path = Path("test-artifacts") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def init_demo_repo(path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required for Aider integration file metadata test")
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    (path / "app.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "init"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def load_trace(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_aider_adapter_captures_terminal_and_file_events():
    root = artifact_dir()
    repo = root / "repo"
    repo.mkdir()
    init_demo_repo(repo)

    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; p=Path('app.py'); p.write_text(p.read_text()+\"\\n# mock aider edit\\n\"); print('Model: gpt-4o-mini with whole edit format'); print('Tokens: 930 sent, 132 received. Cost: $0.00022 message, $0.00022 session.'); print('mock aider changed app.py')",
    ]
    result = capture_aider(
        name="mock aider integration",
        command=command,
        repo_path=repo,
        trace_dir=root / "traces",
    )
    trace = load_trace(result.trace_path)
    event_types = [event["event_type"] for event in trace["events"]]

    assert result.exit_code == 0
    assert trace["task"]["agent_type"] == "aider"
    assert "terminal_event" in event_types
    assert "file_event" in event_types
    assert "model_call_start" in event_types
    assert "model_call_end" in event_types
    assert "tool_call_start" in event_types
    assert "tool_call_end" in event_types

    tool_start = next(event for event in trace["events"] if event["event_type"] == "tool_call_start")
    model_end = next(event for event in trace["events"] if event["event_type"] == "model_call_end")
    file_event = next(event for event in trace["events"] if event["event_type"] == "file_event")
    terminal = next(event for event in trace["events"] if event["event_type"] == "terminal_event")

    assert tool_start["attributes"]["integration"] == "aider"
    assert model_end["attributes"]["input_tokens"] == 930
    assert model_end["attributes"]["output_tokens"] == 132
    assert model_end["attributes"]["cost_dollars"] == 0.00022
    assert file_event["attributes"]["path"] == "app.py"
    assert terminal["payload"]["git_diff_summary"]
    assert "mock aider changed app.py" in terminal["attributes"]["stdout_preview"]


def test_parse_aider_model_metadata_from_realistic_stdout():
    metadata = parse_aider_model_metadata(
        "Aider v0.86.2\nModel: gpt-4o-mini with whole edit format\nTokens: 1,234 sent, 56 received. Cost: $0.00031 message, $0.00031 session.\n"
    )

    assert metadata == {
        "model": "gpt-4o-mini",
        "input_tokens": 1234,
        "output_tokens": 56,
        "cost_dollars": 0.00031,
    }


def test_parse_aider_model_metadata_with_compact_token_counts():
    metadata = parse_aider_model_metadata(
        "Model: gpt-4o-mini with whole edit format\nTokens: 1.0k sent, 110 received. Cost: $0.00022 message, $0.00022 session.\n"
    )

    assert metadata is not None
    assert metadata["input_tokens"] == 1000
    assert metadata["output_tokens"] == 110
    assert metadata["cost_dollars"] == 0.00022
