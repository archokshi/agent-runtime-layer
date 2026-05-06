import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_sample(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def test_backend_aware_runtime_generates_and_persists_hints(client):
    trace = load_sample("v1_5_repeated_context_baseline.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    response = client.post("/api/tasks/task_v1_5_repeated_context_baseline/backend-hints")
    assert response.status_code == 200
    body = response.json()

    assert body["backend_runtime_version"] == "v2.5"
    assert body["mode"] == "backend_agnostic_hint_generation"
    assert body["metrics"]["prefix_overlap_estimate_percent"] >= 30
    assert body["metrics"]["cache_locality"] == "high"
    assert body["metrics"]["prefill_decode_classification"] == "prefill_heavy"
    assert body["backend_registry"]
    assert body["model_call_profiles"]
    assert any(hint["category"] == "cache_locality" for hint in body["routing_hints"])
    assert any(hint["target_backend_id"] == "prefix_cache_capable" for hint in body["routing_hints"])
    assert "does not call real vLLM" in body["notes"]

    persisted = client.get("/api/tasks/task_v1_5_repeated_context_baseline/backend-hints")
    assert persisted.status_code == 200
    assert persisted.json()["metrics"]["prefix_overlap_estimate_percent"] == body["metrics"]["prefix_overlap_estimate_percent"]


def test_backend_aware_runtime_detects_queue_pressure(client):
    trace = load_sample("v2_5_backend_queue_pressure.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    response = client.post("/api/tasks/task_v2_5_backend_queue_pressure/backend-hints")
    assert response.status_code == 200
    body = response.json()

    assert body["metrics"]["queue_depth_observed"] == 7
    assert any(hint["category"] == "queue_depth" for hint in body["routing_hints"])
    queue_hint = next(hint for hint in body["routing_hints"] if hint["category"] == "queue_depth")
    assert queue_hint["title"] == "Avoid saturated backend queue"
    assert "lower queue depth" in queue_hint["action"]
