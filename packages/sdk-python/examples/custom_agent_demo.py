import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_runtime_layer import AgentRuntimeTracer, context_hash, estimate_cost, prompt_hash


def main() -> None:
    repo_context = "repo summary + tool schema"
    expanded_context = "repo summary + tool schema + pytest failure log"
    shared_hash = context_hash(repo_context)

    with AgentRuntimeTracer(task_name="SDK custom agent demo", project_id="default") as trace:
        trace.log_context_snapshot(
            size_tokens=12000,
            repeated_tokens_estimate=0,
            context_kind="repo_summary_plus_tool_schema",
            context_hash_value=shared_hash,
        )

        with trace.model_call(
            model="gpt-5-codex",
            role="planner",
            estimated_input_tokens=12000,
            expected_output_tokens=600,
            prompt_hash_value=prompt_hash("plan fix for failing settings test"),
            name="planner_model_call",
        ) as call:
            time.sleep(0.02)
            call.finish(
                input_tokens=12000,
                output_tokens=520,
                cost_dollars=estimate_cost(12000, 520, input_cost_per_million=1.25, output_cost_per_million=10.0),
            )

        with trace.tool_call(
            tool_name="terminal",
            command="pytest tests/test_settings.py",
            risk_level="medium",
            name="run_tests",
        ) as tool:
            time.sleep(0.01)
            tool.finish(
                status="failed",
                exit_code=1,
                payload={"stdout_preview": "", "stderr_preview": "Expected validation error to be rendered"},
            )

        trace.log_context_snapshot(
            size_tokens=18000,
            repeated_tokens_estimate=12000,
            context_kind="repo_summary_plus_tool_schema_plus_test_log",
            context_hash_value=context_hash(expanded_context),
        )
        trace.log_cache_event(
            reusable_tokens_estimate=12000,
            cache_hit=False,
            reuse_reason="repo summary and tool schema repeated across agent turns",
        )

        trace.end_task(status="completed", summary="Generated a custom SDK trace with model, tool, context, and cache events.")

    print(trace.trace_path)


if __name__ == "__main__":
    main()
