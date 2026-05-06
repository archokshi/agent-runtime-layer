import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def test_hardware_telemetry_import_and_analysis(client):
    trace = load_trace("v1_5_repeated_context_baseline.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    response = client.post("/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import", json=telemetry)
    assert response.status_code == 200
    assert response.json()["sample_count"] == 4

    report = client.get("/api/tasks/task_v1_5_repeated_context_baseline/hardware-analysis")
    assert report.status_code == 200
    body = report.json()

    assert body["hardware_runtime_version"] == "v3.0"
    assert body["mode"] == "imported_telemetry_correlation"
    assert body["summary"]["sample_count"] == 4
    assert body["summary"]["max_queue_depth"] == 6
    assert body["summary"]["avg_gpu_memory_used_percent"] >= 85
    assert body["correlated_windows"]
    categories = {bottleneck["category"] for bottleneck in body["bottlenecks"]}
    assert "queue_saturation" in categories
    assert "memory_pressure" in categories
    assert "cache_miss_pressure" in categories
    assert "prefill_bottleneck" in categories
    assert "does not require live GPU metrics" in body["notes"]


def test_hardware_telemetry_rejects_mismatched_task_id(client):
    trace = load_trace("v1_5_repeated_context_baseline.json")
    assert client.post("/api/traces/import", json=trace).status_code == 200
    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    telemetry["task_id"] = "wrong_task"
    response = client.post("/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import", json=telemetry)
    assert response.status_code == 400


def test_hardware_analysis_detects_gpu_underutilized_with_queue(client):
    trace = load_trace("v2_5_backend_queue_pressure.json")
    imported = client.post("/api/traces/import", json=trace)
    assert imported.status_code == 200

    telemetry = load_telemetry("v3_0_gpu_underutilized_queue.json")
    response = client.post("/api/tasks/task_v2_5_backend_queue_pressure/telemetry/import", json=telemetry)
    assert response.status_code == 200
    assert response.json()["sample_count"] == 3

    report = client.get("/api/tasks/task_v2_5_backend_queue_pressure/hardware-analysis")
    assert report.status_code == 200
    body = report.json()
    assert body["summary"]["avg_gpu_utilization_percent"] < 35
    assert body["summary"]["max_queue_depth"] == 4
    categories = {bottleneck["category"] for bottleneck in body["bottlenecks"]}
    assert "gpu_underutilized" in categories
