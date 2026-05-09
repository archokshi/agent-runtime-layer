import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def test_telemetry_summary_empty_database_is_missing(client):
    response = client.get("/api/telemetry/summary")

    assert response.status_code == 200
    report = response.json()
    assert report["report_version"] == "phase-1.3"
    assert report["mode"] == "backend_telemetry_evidence_readiness"
    assert report["readiness_status"] == "missing"
    assert report["sample_count"] == 0
    assert any("does not poll live GPUs" in item for item in report["limitations"])


def test_telemetry_summary_reports_phase2_backend_evidence(client):
    assert client.post("/api/traces/import", json=load_trace("v1_5_repeated_context_baseline.json")).status_code == 200
    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import", json=telemetry).status_code == 200

    response = client.get("/api/telemetry/summary")

    assert response.status_code == 200
    report = response.json()
    assert report["telemetry_task_count"] == 1
    assert report["sample_count"] == 4
    assert report["backend_count"] == 1
    assert report["readiness_status"] == "partial"

    fields = {item["field"]: item for item in report["field_coverage"]}
    assert fields["gpu_utilization_percent"]["status"] == "ready"
    assert fields["queue_depth"]["status"] == "ready"
    assert fields["prefill_ms"]["status"] == "ready"
    assert fields["decode_ms"]["status"] == "ready"
    assert fields["kv_cache_hit_rate"]["phase2_use"].startswith("Validates whether repeated context")

    needs = {item["need_id"]: item for item in report["phase2_evidence_value"]}
    assert needs["gpu_underutilization"]["phase2_use"].startswith("Tests the YC RFS hypothesis")
    assert needs["prefill_decode_split"]["status"] == "ready"
    assert "queue_saturation" in report["bottleneck_counts"]
    assert "memory_pressure" in report["bottleneck_counts"]
    assert report["task_summaries"][0]["has_prefill_decode"] is True


def test_telemetry_summary_detects_gpu_underutilized_evidence(client):
    assert client.post("/api/traces/import", json=load_trace("v2_5_backend_queue_pressure.json")).status_code == 200
    telemetry = load_telemetry("v3_0_gpu_underutilized_queue.json")
    assert client.post("/api/tasks/task_v2_5_backend_queue_pressure/telemetry/import", json=telemetry).status_code == 200

    response = client.get("/api/telemetry/summary")

    assert response.status_code == 200
    report = response.json()
    assert "gpu_underutilized" in report["bottleneck_counts"]
    assert report["task_summaries"][0]["has_gpu_utilization"] is True
    assert report["task_summaries"][0]["has_queue_depth"] is True
