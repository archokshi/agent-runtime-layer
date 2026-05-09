import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def load_benchmark(name: str) -> dict:
    return json.loads((ROOT / "examples" / "benchmark-runs" / name).read_text())


def test_phase2_handoff_generates_persists_and_exports(client):
    assert client.post("/api/traces/import", json=load_trace("v1_5_repeated_context_baseline.json")).status_code == 200
    assert client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=load_telemetry("v3_0_prefill_queue_pressure.json"),
    ).status_code == 200
    assert client.post("/api/benchmarks/runs", json=load_benchmark("v0_5_swebench_aider_smoke.json")).status_code == 200

    response = client.post("/api/phase-2-handoff/generate")

    assert response.status_code == 200
    package = response.json()
    assert package["handoff_id"].startswith("phase2_handoff_")
    assert package["package_version"] == "phase-1.5"
    assert package["mode"] == "phase_2_handoff_artifact"
    assert package["phase2_entry_criteria_score"] >= 0
    assert package["workload_model_input"]["title"] == "Phase 2.0 Agentic Inference Workload Model"
    assert package["backend_gap_analysis_input"]["title"] == "Phase 2.1 Existing Backend/System/Hardware Gap Analysis"
    assert package["runtime_hardware_interface_input"]["phase2_consumes"]
    assert package["memory_context_architecture_input"]["missing_items"]
    assert package["compiler_execution_graph_input"]["next_steps"]
    assert package["evidence_quality_gate"]["evidence"]["phase2_safety_rules"]
    assert package["phase2_test_plan"]
    assert any("real KV-cache hits" in item for item in package["phase2_do_not_claim"])
    assert any("hardware speedup" in item for item in package["phase2_do_not_claim"])
    assert package["source_reports"]["trace_corpus"]["readiness_score"] >= 0

    listed = client.get("/api/phase-2-handoff")
    assert listed.status_code == 200
    assert listed.json()[0]["handoff_id"] == package["handoff_id"]

    fetched = client.get(f"/api/phase-2-handoff/{package['handoff_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["handoff_id"] == package["handoff_id"]

    markdown = client.get(f"/api/phase-2-handoff/{package['handoff_id']}/export.md")
    assert markdown.status_code == 200
    assert "Phase 1.5 Phase 2 System Blueprint Handoff Package" in markdown.text
    assert "Phase 2.1 Existing Backend/System/Hardware Gap Analysis" in markdown.text
    assert "Do Not Claim" in markdown.text
