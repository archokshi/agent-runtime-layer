import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def load_benchmark(name: str) -> dict:
    return json.loads((ROOT / "examples" / "benchmark-runs" / name).read_text())


def test_evidence_campaign_generates_targets_persists_exports_and_regenerates_handoff(client):
    assert client.post("/api/traces/import", json=load_trace("v1_5_repeated_context_baseline.json")).status_code == 200
    assert client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=load_telemetry("v3_0_prefill_queue_pressure.json"),
    ).status_code == 200
    assert client.post("/api/benchmarks/runs", json=load_benchmark("v0_5_swebench_aider_smoke.json")).status_code == 200

    response = client.post("/api/evidence-campaign/generate")

    assert response.status_code == 200
    report = response.json()
    assert report["campaign_id"].startswith("phase16_campaign_")
    assert report["campaign_version"] == "phase-1.6"
    assert report["mode"] == "evidence_campaign_readiness_report"
    assert report["campaign_score"] > 0
    assert report["campaign_status"] in {"partial", "ready"}
    assert report["regenerated_phase2_handoff_id"].startswith("phase2_handoff_")
    assert report["regenerated_phase2_entry_score"] >= 0

    track_names = {track["name"] for track in report["tracks"]}
    assert "Track A: Real Coding-Agent Runs" in track_names
    assert "Track B: Benchmark-Style Runs" in track_names
    assert "Track C: Before/After Optimization Pairs" in track_names
    assert "Track D: Telemetry Imports, If Available" in track_names

    minimum_ids = {target["target_id"] for target in report["minimum_exit_criteria"]}
    assert "real_coding_agent_traces" in minimum_ids
    assert "benchmark_style_traces" in minimum_ids
    assert "before_after_pairs" in minimum_ids
    assert "outcome_metadata" in minimum_ids

    assert "task_start" in report["required_trace_fields"]
    assert "context_snapshot" in report["required_trace_fields"]
    assert any("KV-cache hits" in item for item in report["no_claims"])
    assert any("hardware speedup" in item for item in report["no_claims"])
    assert report["source_reports"]["phase2_handoff"]["handoff_id"] == report["regenerated_phase2_handoff_id"]

    listed = client.get("/api/evidence-campaign")
    assert listed.status_code == 200
    assert listed.json()[0]["campaign_id"] == report["campaign_id"]

    fetched = client.get(f"/api/evidence-campaign/{report['campaign_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["campaign_id"] == report["campaign_id"]

    markdown = client.get(f"/api/evidence-campaign/{report['campaign_id']}/export.md")
    assert markdown.status_code == 200
    assert "Phase 1.6 Evidence Campaign Report" in markdown.text
    assert "Track A: Real Coding-Agent Runs" in markdown.text
    assert "No Claims" in markdown.text
