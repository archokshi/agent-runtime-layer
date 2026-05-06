import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def load_benchmark(name: str) -> dict:
    return json.loads((ROOT / "examples" / "benchmark-runs" / name).read_text())


def test_phase1_exit_package_generates_persists_and_exports(client):
    assert client.post("/api/traces/import", json=load_trace("v1_5_repeated_context_baseline.json")).status_code == 200
    assert client.post("/api/traces/import", json=load_trace("v2_5_backend_queue_pressure.json")).status_code == 200
    assert client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=load_telemetry("v3_0_prefill_queue_pressure.json"),
    ).status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/optimize-context").status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/schedule").status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/backend-hints").status_code == 200
    assert client.get("/api/tasks/task_v1_5_repeated_context_baseline/hardware-analysis").status_code == 200
    assert client.post("/api/benchmarks/runs", json=load_benchmark("v0_5_swebench_aider_smoke.json")).status_code == 200
    blueprint = client.post(
        "/api/blueprints/generate",
        json={"name": "phase exit blueprint", "task_ids": ["task_v1_5_repeated_context_baseline", "task_v2_5_backend_queue_pressure"]},
    )
    assert blueprint.status_code == 200
    assert client.post(f"/api/blueprints/{blueprint.json()['blueprint_id']}/simulate", json={}).status_code == 200

    response = client.post("/api/phase-1-exit/generate")
    assert response.status_code == 200
    package = response.json()

    assert package["package_id"].startswith("phase1_exit_")
    assert package["package_version"] == "phase-1.011"
    assert package["mode"] == "phase_1_exit_artifact"
    assert package["workload_evaluation_package"]["workload_corpus_summary"]["task_count"] == 2
    assert package["workload_evaluation_package"]["context_kv_reuse_profile"]["avg_repeated_context_percent"] > 0
    assert package["workload_recommendation_package"]["prioritized_recommendations"]
    assert package["metric_quality_scorecard"]
    assert package["architecture_readiness_score"] > 0
    assert package["phase_1_5_hardware_test_plan"]
    assert package["phase_2_architecture_signals"]
    assert any("Do not claim real KV-cache hits" in item for item in package["do_not_do_yet"])

    listed = client.get("/api/phase-1-exit")
    assert listed.status_code == 200
    assert listed.json()[0]["package_id"] == package["package_id"]

    fetched = client.get(f"/api/phase-1-exit/{package['package_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["package_id"] == package["package_id"]

    markdown = client.get(f"/api/phase-1-exit/{package['package_id']}/export.md")
    assert markdown.status_code == 200
    assert "Phase 1.011 Workload Evaluation" in markdown.text
    assert "Phase 1.5 Existing Hardware Test Plan" in markdown.text
    assert "Do Not Do Yet" in markdown.text
