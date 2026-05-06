import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_trace(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-traces" / name).read_text())


def load_telemetry(name: str) -> dict:
    return json.loads((ROOT / "examples" / "sample-telemetry" / name).read_text())


def test_silicon_blueprint_report_generates_and_persists(client):
    traces = [
        load_trace("v1_5_repeated_context_baseline.json"),
        load_trace("v2_5_backend_queue_pressure.json"),
    ]
    for trace in traces:
        response = client.post("/api/traces/import", json=trace)
        assert response.status_code == 200

    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    telemetry_response = client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=telemetry,
    )
    assert telemetry_response.status_code == 200

    response = client.post(
        "/api/blueprints/generate",
        json={
            "name": "test blueprint",
            "task_ids": [
                "task_v1_5_repeated_context_baseline",
                "task_v2_5_backend_queue_pressure",
            ],
        },
    )
    assert response.status_code == 200
    report = response.json()

    assert report["blueprint_version"] == "v3.5"
    assert report["mode"] == "rule_based_architecture_report"
    assert report["workload_profile"]["task_count"] == 2
    assert report["workload_profile"]["total_input_tokens"] > 0
    assert report["memory_hierarchy_recommendations"]
    assert report["hardware_primitive_rankings"]
    assert report["benchmark_proposals"]
    assert report["validation_summary"]["local_trace_count"] == 2
    assert report["validation_summary"]["target_trace_count"] == 100
    assert report["validation_summary"]["tasks_with_hardware_telemetry"] == 1
    assert any(item["primitive"] == "persistent_kv_cache" for item in report["hardware_primitive_rankings"])
    assert any("Not ASIC design" in item for item in report["limitations"])

    persisted = client.get(f"/api/blueprints/{report['blueprint_id']}")
    assert persisted.status_code == 200
    assert persisted.json()["blueprint_id"] == report["blueprint_id"]

    listed = client.get("/api/blueprints")
    assert listed.status_code == 200
    assert listed.json()[0]["blueprint_id"] == report["blueprint_id"]

    markdown = client.get(f"/api/blueprints/{report['blueprint_id']}/export.md")
    assert markdown.status_code == 200
    assert "# test blueprint" in markdown.text
    assert "## Hardware Primitive Ranking" in markdown.text
    assert "Not ASIC design" in markdown.text


def test_trace_replay_simulator_projects_core_scenarios(client):
    traces = [
        load_trace("v1_5_repeated_context_baseline.json"),
        load_trace("v2_5_backend_queue_pressure.json"),
    ]
    for trace in traces:
        assert client.post("/api/traces/import", json=trace).status_code == 200

    telemetry = load_telemetry("v3_0_prefill_queue_pressure.json")
    assert client.post(
        "/api/tasks/task_v1_5_repeated_context_baseline/telemetry/import",
        json=telemetry,
    ).status_code == 200

    blueprint_response = client.post(
        "/api/blueprints/generate",
        json={
            "name": "replay test blueprint",
            "task_ids": [
                "task_v1_5_repeated_context_baseline",
                "task_v2_5_backend_queue_pressure",
            ],
        },
    )
    assert blueprint_response.status_code == 200
    blueprint_id = blueprint_response.json()["blueprint_id"]

    replay_response = client.post(f"/api/blueprints/{blueprint_id}/simulate", json={})
    assert replay_response.status_code == 200
    replay = replay_response.json()

    assert replay["simulator_version"] == "v4.5"
    assert replay["mode"] == "rule_based_trace_replay_projection"
    scenario_ids = {scenario["scenario_id"] for scenario in replay["scenario_results"]}
    assert {"persistent_prefix_cache", "tool_wait_scheduler", "prefill_decode_split"} <= scenario_ids
    assert replay["best_scenario_id"] in scenario_ids
    assert all("Projection only" in scenario["notes"] for scenario in replay["scenario_results"])
    assert any("No hardware simulation" in item for item in replay["limitations"])

    listed = client.get(f"/api/blueprints/{blueprint_id}/replays")
    assert listed.status_code == 200
    assert listed.json()[0]["replay_id"] == replay["replay_id"]

    fetched = client.get(f"/api/replays/{replay['replay_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["replay_id"] == replay["replay_id"]


def test_trace_replay_simulator_supports_all_scenarios_and_markdown_export(client):
    for trace in [load_trace("v1_5_repeated_context_baseline.json"), load_trace("v2_5_backend_queue_pressure.json")]:
        assert client.post("/api/traces/import", json=trace).status_code == 200

    blueprint_response = client.post(
        "/api/blueprints/generate",
        json={
            "name": "all scenario blueprint",
            "task_ids": [
                "task_v1_5_repeated_context_baseline",
                "task_v2_5_backend_queue_pressure",
            ],
        },
    )
    assert blueprint_response.status_code == 200
    blueprint_id = blueprint_response.json()["blueprint_id"]
    scenario_ids = [
        "persistent_prefix_cache",
        "tool_wait_scheduler",
        "prefill_decode_split",
        "warm_context_tier",
        "kv_compression",
    ]

    replay_response = client.post(
        f"/api/blueprints/{blueprint_id}/simulate",
        json={"scenario_ids": scenario_ids},
    )
    assert replay_response.status_code == 200
    replay = replay_response.json()

    assert replay["simulator_version"] == "v4.5"
    assert replay["scenario_selection"] == scenario_ids
    assert {scenario["scenario_id"] for scenario in replay["scenario_results"]} == set(scenario_ids)
    assert replay["comparison_summary"]["scenario_count"] == 5
    for scenario in replay["scenario_results"]:
        assert scenario["projection_confidence_reason"]
        assert scenario["requires_real_backend_validation"] is True
        assert scenario["validation_evidence_needed"]

    markdown = client.get(f"/api/replays/{replay['replay_id']}/export.md")
    assert markdown.status_code == 200
    assert "## Comparison Summary" in markdown.text
    assert "Validation evidence needed" in markdown.text
