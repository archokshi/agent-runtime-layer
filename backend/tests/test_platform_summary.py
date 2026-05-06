import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def test_platform_summary_aggregates_existing_runtime_layers(client):
    trace = load_trace("v1_5_repeated_context_baseline.json")
    assert client.post("/api/traces/import", json=trace).status_code == 200
    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import", json=telemetry).status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/optimize-context").status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/schedule").status_code == 200
    assert client.post("/api/tasks/task_v1_5_repeated_context_baseline/backend-hints").status_code == 200
    assert client.get("/api/tasks/task_v1_5_repeated_context_baseline/hardware-analysis").status_code == 200
    blueprint = client.post(
        "/api/blueprints/generate",
        json={"name": "platform test blueprint", "task_ids": ["task_v1_5_repeated_context_baseline"]},
    )
    assert blueprint.status_code == 200
    blueprint_id = blueprint.json()["blueprint_id"]
    replay = client.post(f"/api/blueprints/{blueprint_id}/simulate", json={})
    assert replay.status_code == 200
    experiment = client.post(
        "/api/validation/experiments",
        json={
            "scenario_id": "persistent_prefix_cache",
            "scenario_name": "v1.5 real OpenAI repeated-context validation",
            "baseline_task_id": "task_v1_5_real_context_baseline_203c3d6d",
            "optimized_task_id": "task_v1_5_real_context_optimized_203c3d6d",
            "projected_input_token_reduction_percent": 30.9,
            "measured_input_token_reduction_percent": 33.73,
            "projected_cost_reduction_percent": 10.67,
            "measured_cost_reduction_percent": 10.67,
            "success_preserved": True,
            "evidence": "Controlled real OpenAI run measured input tokens from 424 to 281.",
            "notes": "Measured token/cost validation only; no real KV-cache hit or hardware speedup claimed.",
        },
    )
    assert experiment.status_code == 200
    benchmark = client.post(
        "/api/benchmarks/runs",
        json={
            "suite_name": "aider",
            "suite_version": "local-smoke",
            "agent_name": "aider-openai",
            "run_mode": "smoke",
            "task_results": [
                {
                    "benchmark_task_id": "aider-local-001",
                    "task_id": "task_v1_5_repeated_context_baseline",
                    "trace_complete": True,
                    "task_success": True,
                    "tests_passed": 3,
                    "tests_failed": 0,
                    "patch_generated": True,
                    "model_call_count": 1,
                    "tool_call_count": 2,
                    "retry_count": 0,
                    "total_cost_dollars": 0.001,
                    "duration_seconds": 12.0,
                    "top_bottleneck": "Repeated Context",
                    "actionable_recommendation": True,
                }
            ],
            "limitations": ["Local smoke record only."],
        },
    )
    assert benchmark.status_code == 200

    response = client.get("/api/platform/summary")
    assert response.status_code == 200
    summary = response.json()

    assert summary["platform_version"] == "v5.0"
    assert summary["mode"] == "local_project_readiness_overview"
    assert summary["latest_blueprint_id"] == blueprint_id
    assert summary["latest_replay_id"] == replay.json()["replay_id"]
    assert summary["measured_validation"][0]["experiment_id"] == experiment.json()["experiment_id"]
    assert summary["measured_validation"][0]["projection_error_percent"] == 2.83
    assert summary["benchmark_suite"]["run_count"] == 1
    assert summary["benchmark_suite"]["task_count"] == 1
    assert {item["module"] for item in summary["module_coverage"]} >= {"Traces", "Blueprints", "Replays", "Benchmark Suite"}
    assert {item["category"] for item in summary["readiness"]} >= {"Optimization", "Backend Validation", "Silicon Blueprint"}
    assert {step["step_id"] for step in summary["runbook"]} >= {"trace", "analyze", "optimize", "schedule", "backend", "telemetry", "blueprint", "replay"}
    assert any("not a cloud SaaS" in item for item in summary["limitations"])
