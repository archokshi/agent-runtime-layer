import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_sample(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def test_import_trace_creates_task_events_analysis_and_blueprint(client):
    trace = load_sample("repeated-context-task.json")
    response = client.post("/api/traces/import", json=trace)
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task_repeated_context_001"
    assert body["event_count"] == 12

    events = client.get(f"/api/tasks/{body['task_id']}/events").json()
    assert [event["event_id"] for event in events] == [f"evt_{index:03d}" for index in range(1, 13)]

    analysis = client.get(f"/api/tasks/{body['task_id']}/analysis").json()
    assert analysis["total_task_duration_ms"] == 45000
    assert analysis["model_time_ms"] == 10700
    assert analysis["tool_time_ms"] == 20000
    assert analysis["total_input_tokens"] == 40000
    assert analysis["estimated_total_cost_dollars"] == 0.123
    assert analysis["bottleneck_category"] in {"repeated_context", "tool_wait"}

    blueprint = client.get(f"/api/tasks/{body['task_id']}/blueprint").json()
    titles = {rec["title"] for rec in blueprint["recommendations"]}
    assert "Persistent KV/prefix cache recommended" in titles
    assert "Warm context tier recommended" in titles

    optimizations = client.get(f"/api/tasks/{body['task_id']}/optimizations").json()
    opt_titles = {rec["title"] for rec in optimizations["recommendations"]}
    assert "Cache repeated context prefixes" in opt_titles
    assert all("confidence" in rec for rec in optimizations["recommendations"])
    assert all("action" in rec for rec in optimizations["recommendations"])


def test_redacts_obvious_secrets_before_storage(client):
    task = client.post("/api/tasks", json={"goal": "Check redaction"}).json()
    event = {
        "event_id": "evt_secret",
        "task_id": task["task_id"],
        "timestamp": "2026-05-03T10:00:00.000Z",
        "event_type": "terminal_event",
        "span_id": "span_secret",
        "parent_span_id": None,
        "name": "terminal",
        "attributes": {"command": "echo api_key=abc123 password=hunter2 sk-testsecret999"},
        "payload": {"stdout_preview": "token=abc secret=xyz"},
    }
    assert client.post("/api/events", json=event).status_code == 200
    stored = client.get(f"/api/tasks/{task['task_id']}/events").json()[0]
    serialized = json.dumps(stored)
    assert "hunter2" not in serialized
    assert "sk-testsecret999" not in serialized
    assert "[REDACTED]" in serialized


def test_otel_export_and_import_preserve_analyzable_trace(client):
    trace = load_sample("successful-coding-task.json")
    imported = client.post("/api/traces/import", json=trace).json()

    otel_response = client.get(f"/api/tasks/{imported['task_id']}/otel")
    assert otel_response.status_code == 200
    otel = otel_response.json()
    resource_attrs = otel["resourceSpans"][0]["resource"]["attributes"]
    assert any(attr["key"] == "arl.task_id" for attr in resource_attrs)
    spans = otel["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert len(spans) == imported["event_count"]
    assert all(span["traceId"] for span in spans)
    assert all(span["spanId"] for span in spans)

    reimported = client.post("/api/traces/import/otel", json=otel)
    assert reimported.status_code == 200
    body = reimported.json()
    assert body["task_id"] == imported["task_id"]
    assert body["event_count"] == imported["event_count"]

    analysis = client.get(f"/api/tasks/{body['task_id']}/analysis").json()
    assert analysis["model_call_count"] >= 1
    assert analysis["tool_call_count"] >= 1


def test_optimization_recommendations_include_tool_wait(client):
    trace = load_sample("slow-tool-heavy-task.json")
    imported = client.post("/api/traces/import", json=trace).json()

    optimizations = client.get(f"/api/tasks/{imported['task_id']}/optimizations")
    assert optimizations.status_code == 200
    titles = {rec["title"] for rec in optimizations.json()["recommendations"]}
    assert "Reduce blocking tool wait" in titles


def test_validation_before_after_report(client):
    baseline = load_sample("swebench-style-baseline.json")
    optimized = load_sample("swebench-style-optimized.json")
    baseline_response = client.post("/api/traces/import", json=baseline)
    optimized_response = client.post("/api/traces/import", json=optimized)
    assert baseline_response.status_code == 200
    assert optimized_response.status_code == 200

    report = client.get("/api/tasks/task_swebench_optimized_001/validation")
    assert report.status_code == 200
    body = report.json()
    assert body["metadata"]["benchmark_name"] == "swebench-lite-mini"
    assert body["metadata"]["task_success"] is True
    assert body["metadata"]["patch_generated"] is True
    assert body["comparison"]["before_after_pair_id"] == "pair_swebench_001"
    assert body["comparison"]["baseline_task_id"] == "task_swebench_baseline_001"
    assert body["comparison"]["optimized_task_id"] == "task_swebench_optimized_001"
    assert body["comparison"]["success_preserved"] is True
    assert body["comparison"]["repeated_input_token_reduction_percent"] == 75.0
    assert body["comparison"]["estimated_cost_reduction_percent"] > 0


def test_validation_retry_loop_sample_imports(client):
    trace = load_sample("aider-style-retry-loop.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    analysis = client.get("/api/tasks/task_aider_retry_validation_001/analysis").json()
    validation = client.get("/api/tasks/task_aider_retry_validation_001/validation").json()
    assert analysis["retry_count"] >= 1
    assert validation["metadata"]["agent_name"] == "aider"
    assert validation["metadata"]["tests_passed"] == 3
