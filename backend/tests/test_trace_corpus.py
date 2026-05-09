import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def test_trace_corpus_empty_database_is_missing_not_ready(client):
    response = client.get("/api/corpus/summary")

    assert response.status_code == 200
    report = response.json()
    assert report["report_version"] == "phase-1.1"
    assert report["mode"] == "phase_2_evidence_corpus_readiness"
    assert report["readiness_status"] == "missing"
    assert report["readiness_score"] == 0
    assert report["target_trace_count"] == 100
    assert any("not hardware validation" in item for item in report["limitations"])


def test_trace_corpus_reports_phase2_evidence_from_imported_trace(client):
    trace = load_trace("v1_5_repeated_context_baseline.json")
    assert client.post("/api/traces/import", json=trace).status_code == 200

    response = client.get("/api/corpus/summary")

    assert response.status_code == 200
    report = response.json()
    assert report["readiness_status"] == "partial"
    assert report["metrics"][0]["value"] == "1/100"
    assert report["task_summaries"][0]["task_id"] == "task_v1_5_repeated_context_baseline"
    assert report["task_summaries"][0]["has_model_events"] is True
    assert report["task_summaries"][0]["has_tool_events"] is True
    assert report["task_summaries"][0]["has_context_snapshots"] is True
    assert report["task_summaries"][0]["has_outcome_metadata"] is True
    assert report["task_summaries"][0]["phase2_value"] == "model/tool split, context lifetime, outcome distribution"

    needs = {item["need_id"]: item for item in report["phase2_evidence_needs"]}
    assert needs["execution_graph_shapes"]["status"] in {"ready", "partial"}
    assert needs["context_lifetime"]["phase2_use"].startswith("Feeds persistent context")
    assert needs["model_tool_cpu_io_split"]["phase2_use"].startswith("Explains the GPU utilization collapse")
    assert needs["retry_backtrack_frequency"]["status"] == "missing"


def test_trace_corpus_tracks_benchmark_and_retry_metadata(client):
    trace = load_trace("aider-style-retry-loop.json")
    assert client.post("/api/traces/import", json=trace).status_code == 200

    response = client.get("/api/corpus/summary")

    assert response.status_code == 200
    report = response.json()
    coverage = {item["category"]: item for item in report["coverage"]}
    assert coverage["Trace volume"]["status"] == "partial"
    assert coverage["Benchmark-linked traces"]["count"] >= 1

    needs = {item["need_id"]: item for item in report["phase2_evidence_needs"]}
    assert needs["retry_backtrack_frequency"]["status"] in {"ready", "partial"}
    assert any("No real KV-cache hit" in item for item in report["limitations"])
