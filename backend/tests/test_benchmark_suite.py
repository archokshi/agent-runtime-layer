def benchmark_payload():
    return {
        "suite_name": "swe-bench-lite",
        "suite_version": "smoke-0",
        "agent_name": "aider",
        "agent_version": "local-adapter",
        "run_mode": "smoke",
        "source": "local imported smoke record",
        "task_results": [
            {
                "benchmark_task_id": "django__django-0001",
                "repo_name": "django/django",
                "issue_id": "0001",
                "task_id": "task_swebench_smoke_001",
                "trace_complete": True,
                "task_success": True,
                "tests_passed": 3,
                "tests_failed": 0,
                "patch_generated": True,
                "model_call_count": 2,
                "tool_call_count": 4,
                "retry_count": 1,
                "total_cost_dollars": 0.0123,
                "duration_seconds": 92.0,
                "top_bottleneck": "Tool Wait",
                "actionable_recommendation": True,
            },
            {
                "benchmark_task_id": "sympy__sympy-0002",
                "repo_name": "sympy/sympy",
                "issue_id": "0002",
                "trace_complete": False,
                "task_success": False,
                "tests_passed": 0,
                "tests_failed": 1,
                "patch_generated": False,
                "model_call_count": 1,
                "tool_call_count": 2,
                "retry_count": 2,
                "total_cost_dollars": 0.004,
                "duration_seconds": 55.0,
                "top_bottleneck": "Retry Loop",
                "actionable_recommendation": True,
            },
        ],
        "limitations": [
            "Smoke record only; not an official SWE-bench score.",
        ],
    }


def test_benchmark_suite_run_and_summary(client):
    response = client.post("/api/benchmarks/runs", json=benchmark_payload())
    assert response.status_code == 200
    run = response.json()
    assert run["benchmark_run_id"].startswith("benchmark_")
    assert run["metrics"]["task_count"] == 2
    assert run["metrics"]["trace_completion_rate_percent"] == 50.0
    assert run["metrics"]["task_success_rate_percent"] == 50.0
    assert run["metrics"]["actionable_recommendation_rate_percent"] == 100.0
    assert run["metrics"]["avg_retry_count"] == 1.5

    list_response = client.get("/api/benchmarks/runs")
    assert list_response.status_code == 200
    assert list_response.json()[0]["benchmark_run_id"] == run["benchmark_run_id"]

    summary_response = client.get("/api/benchmarks/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["run_count"] == 1
    assert summary["task_count"] == 2
    assert summary["suite_counts"] == {"swe-bench-lite": 1}
    assert summary["trace_completion_rate_percent"] == 50.0
    assert any("does not download SWE-bench" in item for item in summary["limitations"])
