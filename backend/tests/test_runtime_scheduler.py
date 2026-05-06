import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_sample(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def test_runtime_scheduler_generates_and_persists_decisions(client):
    trace = load_sample("slow-tool-heavy-task.json")
    trace["task"]["latency_slo_seconds"] = 20
    trace["task"]["budget_dollars"] = 0.001
    trace["task"]["priority"] = "foreground"
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    response = client.post("/api/tasks/task_tool_wait_001/schedule")
    assert response.status_code == 200
    body = response.json()

    assert body["scheduler_version"] == "v2.0"
    assert body["mode"] == "local_deterministic_simulation"
    assert body["task_priority"] == "foreground"
    assert body["metrics"]["estimated_time_savings_ms"] > 0
    assert body["metrics"]["scheduled_estimated_duration_ms"] < body["metrics"]["naive_duration_ms"]
    assert body["metrics"]["scheduled_tasks_per_hour"] > body["metrics"]["naive_tasks_per_hour"]
    assert any(decision["category"] == "tool_wait" for decision in body["decisions"])
    assert "does not run a production multi-agent scheduler" in body["notes"]

    persisted = client.get("/api/tasks/task_tool_wait_001/schedule")
    assert persisted.status_code == 200
    assert persisted.json()["metrics"]["estimated_time_savings_ms"] == body["metrics"]["estimated_time_savings_ms"]
