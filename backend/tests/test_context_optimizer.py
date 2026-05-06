import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_sample(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def test_context_optimizer_detects_blocks_and_savings(client):
    trace = load_sample("v1_5_repeated_context_baseline.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    response = client.post("/api/tasks/task_v1_5_repeated_context_baseline/optimize-context")
    assert response.status_code == 200
    body = response.json()

    assert body["optimizer_version"] == "v1.5"
    assert body["baseline"]["input_tokens"] == 40000
    assert body["optimized"]["input_tokens"] == 28000
    assert body["savings"]["input_token_reduction_percent"] == 30.0
    assert body["savings"]["estimated_cost_reduction_percent"] == 30.0
    assert body["savings"]["estimated_prefill_reduction_percent"] == 30.0
    assert body["stable_context_blocks"]
    assert body["dynamic_context_blocks"]
    assert body["optimized_prompt_package"]["stable_prefix_refs"]
    assert "does not claim actual KV-cache hits" in body["optimized_prompt_package"]["notes"]
    assert body["validation"]["task_success_preserved"] is True

    persisted = client.get("/api/tasks/task_v1_5_repeated_context_baseline/optimized-context")
    assert persisted.status_code == 200
    assert persisted.json()["savings"]["input_token_reduction_percent"] == 30.0
