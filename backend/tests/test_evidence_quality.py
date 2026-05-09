import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def test_evidence_quality_empty_database_is_missing(client):
    response = client.get("/api/evidence/quality")

    assert response.status_code == 200
    report = response.json()
    assert report["report_version"] == "phase-1.4"
    assert report["mode"] == "metric_confidence_and_no_overclaiming"
    assert report["overall_status"] in {"missing", "partial"}
    assert "Measured hardware speedup" in report["missing_evidence"]
    assert any("must not use missing metrics" in rule for rule in report["phase2_safety_rules"])


def test_evidence_quality_labels_measured_estimated_and_missing_metrics(client):
    assert client.post("/api/traces/import", json=load_trace("v1_5_repeated_context_baseline.json")).status_code == 200
    assert client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=load_telemetry("v3_0_prefill_queue_pressure.json"),
    ).status_code == 200

    response = client.get("/api/evidence/quality")

    assert response.status_code == 200
    report = response.json()
    categories = {category["category"]: category for category in report["categories"]}
    assert categories["Trace Evidence"]["status"] == "ready"
    trace_metrics = {metric["metric_id"]: metric for metric in categories["Trace Evidence"]["metrics"]}
    assert trace_metrics["trace_count"]["quality"] == "measured"
    assert trace_metrics["model_tool_spans"]["quality"] == "measured"

    optimization_metrics = {metric["metric_id"]: metric for metric in categories["Optimization Evidence"]["metrics"]}
    assert optimization_metrics["model_cost"]["quality"] == "estimated"
    assert optimization_metrics["repeated_context"]["risk_if_overclaimed"].startswith("Repeated-token estimates")

    telemetry_metrics = {metric["metric_id"]: metric for metric in categories["Backend/System Telemetry Evidence"]["metrics"]}
    assert telemetry_metrics["gpu_utilization"]["quality"] == "measured"
    assert telemetry_metrics["kv_cache_hit_rate"]["quality"] == "measured"
    assert telemetry_metrics["hardware_speedup"]["quality"] == "missing"
    assert "Measured hardware speedup" in report["missing_evidence"]
