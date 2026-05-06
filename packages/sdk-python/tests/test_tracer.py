import json
import time
from pathlib import Path
from uuid import uuid4

from agent_runtime_layer import AgentRuntimeTracer, context_hash, estimate_cost, prompt_hash


def trace_dir():
    path = Path("test-artifacts") / uuid4().hex / "traces"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_trace(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_tracer_context_managers_generate_model_tool_context_trace():
    shared_context_hash = context_hash("repo summary")
    with AgentRuntimeTracer(task_name="sdk test", trace_dir=trace_dir()) as trace:
        trace.log_context_snapshot(
            size_tokens=1000,
            context_kind="repo_summary",
            context_hash_value=shared_context_hash,
        )
        trace.log_context_snapshot(
            size_tokens=1200,
            context_kind="repo_summary_plus_log",
            context_hash_value=shared_context_hash,
        )
        with trace.model_call(
            model="gpt-5-codex",
            role="planner",
            estimated_input_tokens=1200,
            expected_output_tokens=100,
            prompt_hash_value=prompt_hash("hello"),
        ) as model:
            time.sleep(0.001)
            model.finish(input_tokens=1200, output_tokens=80, cost_dollars=0.01)
        with trace.tool_call(tool_name="terminal", command="pytest tests/", risk_level="medium") as tool:
            time.sleep(0.001)
            tool.finish(status="success", exit_code=0, payload={"stdout_preview": "passed"})

    stored = load_trace(trace.trace_path)
    event_types = [event["event_type"] for event in stored["events"]]
    assert event_types.count("task_start") == 1
    assert event_types.count("task_end") == 1
    assert event_types.count("context_snapshot") == 2
    assert "model_call_start" in event_types
    assert "model_call_end" in event_types
    assert "tool_call_start" in event_types
    assert "tool_call_end" in event_types
    assert "terminal_event" in event_types

    contexts = [event for event in stored["events"] if event["event_type"] == "context_snapshot"]
    assert contexts[0]["attributes"]["repeated_tokens_estimate"] == 0
    assert contexts[1]["attributes"]["repeated_tokens_estimate"] == 1000


def test_log_helpers_and_cache_event_generate_expected_fields():
    with AgentRuntimeTracer(task_name="sdk helper test", trace_dir=trace_dir()) as trace:
        trace.log_model_call(
            model="gpt-5-codex",
            role="executor",
            input_tokens=5000,
            output_tokens=300,
            latency_ms=1234,
            cost_dollars=estimate_cost(5000, 300, 1.0, 8.0),
            prompt_hash_value=prompt_hash("execute"),
        )
        trace.log_tool_call(
            tool_name="terminal",
            command="pytest",
            latency_ms=2500,
            status="failed",
            exit_code=1,
        )
        trace.log_cache_event(reusable_tokens_estimate=2500, cache_hit=False)

    stored = load_trace(trace.trace_path)
    model_end = next(event for event in stored["events"] if event["event_type"] == "model_call_end")
    tool_end = next(event for event in stored["events"] if event["event_type"] == "tool_call_end")
    cache_event = next(event for event in stored["events"] if event["event_type"] == "cache_event")

    assert model_end["attributes"]["input_tokens"] == 5000
    assert model_end["attributes"]["cost_dollars"] == 0.0074
    assert tool_end["attributes"]["status"] == "failed"
    assert cache_event["attributes"]["reusable_tokens_estimate"] == 2500
