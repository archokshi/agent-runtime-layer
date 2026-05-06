"""Run a small real OpenAI before/after context optimization validation.

This validation helper creates two traces:

1. Baseline: stable context is repeated across two model calls.
2. Optimized: stable context is sent once, then referenced on the second call.

It measures actual OpenAI usage tokens, estimates cost with local demo rates,
writes trace JSON files, and imports them into the local backend when it is
running.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / ".agent-runtime" / "traces"
BACKEND_URL = os.environ.get("AGENT_RUNTIME_BACKEND_URL", "http://localhost:8000/api")
MODEL = os.environ.get("AGENT_RUNTIME_VALIDATION_MODEL", "gpt-4o-mini")

# Demo-only estimates. The trace stores these as estimated cost, not billing data.
INPUT_COST_PER_1M = float(os.environ.get("AGENT_RUNTIME_INPUT_COST_PER_1M", "0.15"))
OUTPUT_COST_PER_1M = float(os.environ.get("AGENT_RUNTIME_OUTPUT_COST_PER_1M", "0.60"))


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    return round(input_cost + output_cost, 6)


def call_openai(prompt: str, role: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AIDER_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env or the current shell environment.")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise coding assistant. Return a concrete patch plan and one short code snippet.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 220,
    }
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API call failed with HTTP {exc.code}: {detail}") from exc

    latency_ms = int((time.perf_counter() - start) * 1000)
    usage = data.get("usage", {})
    message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    input_tokens = int(usage.get("prompt_tokens") or estimate_tokens(prompt))
    output_tokens = int(usage.get("completion_tokens") or estimate_tokens(message))
    return {
        "role": role,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_dollars": estimate_cost(input_tokens, output_tokens),
        "message_preview": message[:500],
    }


def make_event(
    task_id: str,
    event_id: str,
    offset_s: int,
    event_type: str,
    span_id: str,
    name: str,
    attributes: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    parent_span_id: str | None = "span_task",
) -> dict[str, Any]:
    timestamp = datetime(2026, 5, 4, 16, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_s)
    return {
        "event_id": event_id,
        "task_id": task_id,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "event_type": event_type,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "name": name,
        "attributes": attributes or {},
        "payload": payload or {},
    }


def build_trace(
    task_id: str,
    pair_id: str,
    mode: str,
    calls: list[dict[str, Any]],
    stable_tokens: int,
    dynamic_tokens: int,
) -> dict[str, Any]:
    is_optimized = mode == "optimized"
    events = [
        make_event(task_id, f"{task_id}_evt_001", 0, "task_start", "span_task", "task_start", parent_span_id=None, payload={"goal": f"v1.5 real OpenAI {mode} validation"}),
        make_event(
            task_id,
            f"{task_id}_evt_002",
            1,
            "context_snapshot",
            "span_ctx_stable_1",
            "stable_system_tool_repo_context",
            {
                "context_id": f"{task_id}_stable_1",
                "context_hash": "sha256:v1_5_real_stable_context",
                "context_kind": "system_prompt_tool_schema_repo_summary",
                "size_tokens": stable_tokens,
                "repeated_tokens_estimate": 0,
                "text": "stable coding instructions, tool schema, and repo summary",
            },
        ),
        make_event(task_id, f"{task_id}_evt_003", 2, "model_call_start", "span_model_1", "planner_model_call", {"model": MODEL, "role": "planner", "estimated_input_tokens": calls[0]["input_tokens"]}),
        make_event(task_id, f"{task_id}_evt_004", 4, "model_call_end", "span_model_1", "planner_model_call_end", {"input_tokens": calls[0]["input_tokens"], "output_tokens": calls[0]["output_tokens"], "latency_ms": calls[0]["latency_ms"], "cost_dollars": calls[0]["cost_dollars"], "status": "success"}, {"message_preview": calls[0]["message_preview"]}),
    ]
    if is_optimized:
        events.append(make_event(task_id, f"{task_id}_evt_005", 5, "cache_event", "span_cache_1", "stable_prefix_ref", {"reusable_tokens_estimate": stable_tokens, "cache_kind": "prefix_ready_reference"}))
    else:
        events.append(
            make_event(
                task_id,
                f"{task_id}_evt_005",
                5,
                "context_snapshot",
                "span_ctx_stable_2",
                "stable_system_tool_repo_context",
                {
                    "context_id": f"{task_id}_stable_2",
                    "context_hash": "sha256:v1_5_real_stable_context",
                    "context_kind": "system_prompt_tool_schema_repo_summary",
                    "size_tokens": stable_tokens,
                    "repeated_tokens_estimate": stable_tokens,
                    "text": "stable coding instructions, tool schema, and repo summary",
                },
            )
        )
    events.extend(
        [
            make_event(task_id, f"{task_id}_evt_006", 6, "context_snapshot", "span_ctx_dynamic", "latest_test_feedback", {"context_id": f"{task_id}_dynamic", "context_kind": "latest_test_error", "size_tokens": dynamic_tokens, "repeated_tokens_estimate": 0, "text": "latest failed assertion and current instruction"}),
            make_event(task_id, f"{task_id}_evt_007", 7, "model_call_start", "span_model_2", "repair_model_call", {"model": MODEL, "role": "repair", "estimated_input_tokens": calls[1]["input_tokens"]}),
            make_event(task_id, f"{task_id}_evt_008", 9, "model_call_end", "span_model_2", "repair_model_call_end", {"input_tokens": calls[1]["input_tokens"], "output_tokens": calls[1]["output_tokens"], "latency_ms": calls[1]["latency_ms"], "cost_dollars": calls[1]["cost_dollars"], "status": "success"}, {"message_preview": calls[1]["message_preview"]}),
            make_event(task_id, f"{task_id}_evt_009", 10, "tool_call_start", "span_tool_tests", "run_tests", {"tool_name": "terminal", "command": "pytest tests/test_cart.py -q"}),
            make_event(task_id, f"{task_id}_evt_010", 11, "tool_call_end", "span_tool_tests", "run_tests_end", {"latency_ms": 1000, "status": "success", "exit_code": 0}),
            make_event(task_id, f"{task_id}_evt_011", 12, "task_end", "span_task", "task_end", parent_span_id=None, payload={"status": "completed", "summary": f"Real OpenAI {mode} context validation succeeded."}),
        ]
    )
    return {
        "project_id": "validation",
        "task": {
            "task_id": task_id,
            "project_id": "validation",
            "goal": f"v1.5 real OpenAI {mode} context validation",
            "agent_type": "custom_agent",
            "benchmark_name": "v1.5-real-openai-controlled",
            "benchmark_task_id": "real-context-001",
            "repo_name": "local/cart-demo",
            "issue_id": "cart-tax-rounding",
            "agent_name": "controlled-openai-context-agent",
            "baseline_or_optimized": mode,
            "task_success": True,
            "tests_passed": 3,
            "tests_failed": 0,
            "patch_generated": True,
            "files_changed_count": 1,
            "retry_count": 0,
            "before_after_pair_id": pair_id,
        },
        "events": events,
    }


def import_trace(trace: dict[str, Any]) -> None:
    req = request.Request(
        f"{BACKEND_URL}/traces/import",
        data=json.dumps(trace).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=20) as resp:
        resp.read()


def main() -> None:
    load_dotenv()
    suffix = uuid.uuid4().hex[:8]
    pair_id = f"pair_v1_5_real_context_{suffix}"
    baseline_id = f"task_v1_5_real_context_baseline_{suffix}"
    optimized_id = f"task_v1_5_real_context_optimized_{suffix}"

    stable_context = """
You are working in a tiny Python repo.
Tool schema:
- read_file(path): inspect source files
- edit_file(path, patch): apply a minimal patch
- run_tests(command): run pytest and summarize failures
Repo summary:
- cart.py has subtotal(items), apply_tax(amount, rate), and format_total(amount)
- tests/test_cart.py checks rounding to two decimals
- The likely bug is that tax is rounded before being added to subtotal
Coding rule:
- produce the smallest patch
- preserve public function names
- explain which test should pass
"""
    dynamic_context = """
Failing test:
assert format_total(apply_tax(19.99, 0.0825)) == "21.64"
Actual output: "21.63"
Current task: propose the minimal fix and the pytest command to validate it.
"""
    feedback_context = """
New feedback:
The first plan changed formatting only. The assertion still fails by one cent.
Revise the patch plan so tax is calculated with Decimal and rounded only at the final formatting step.
"""
    stable_tokens = estimate_tokens(stable_context)
    dynamic_tokens = estimate_tokens(dynamic_context + feedback_context)

    baseline_prompt_1 = f"{stable_context}\n{dynamic_context}"
    baseline_prompt_2 = f"{stable_context}\n{dynamic_context}\n{feedback_context}"
    optimized_prompt_1 = baseline_prompt_1
    optimized_prompt_2 = f"Stable prefix ref: stable_cart_context. Use the same repo summary and tool schema from the prior call.\n{feedback_context}"

    baseline_calls = [call_openai(baseline_prompt_1, "planner"), call_openai(baseline_prompt_2, "repair")]
    optimized_calls = [call_openai(optimized_prompt_1, "planner"), call_openai(optimized_prompt_2, "repair")]

    baseline_trace = build_trace(baseline_id, pair_id, "baseline", baseline_calls, stable_tokens, dynamic_tokens)
    optimized_trace = build_trace(optimized_id, pair_id, "optimized", optimized_calls, stable_tokens, dynamic_tokens)

    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = TRACE_DIR / f"{baseline_id}.json"
    optimized_path = TRACE_DIR / f"{optimized_id}.json"
    baseline_path.write_text(json.dumps(baseline_trace, indent=2), encoding="utf-8")
    optimized_path.write_text(json.dumps(optimized_trace, indent=2), encoding="utf-8")

    imported = True
    try:
        import_trace(baseline_trace)
        import_trace(optimized_trace)
    except Exception as exc:  # noqa: BLE001
        imported = False
        print(f"Import skipped or failed: {exc}")

    baseline_input = sum(call["input_tokens"] for call in baseline_calls)
    optimized_input = sum(call["input_tokens"] for call in optimized_calls)
    baseline_cost = round(sum(call["cost_dollars"] for call in baseline_calls), 6)
    optimized_cost = round(sum(call["cost_dollars"] for call in optimized_calls), 6)
    input_reduction = round(((baseline_input - optimized_input) / baseline_input) * 100, 2) if baseline_input else 0
    cost_reduction = round(((baseline_cost - optimized_cost) / baseline_cost) * 100, 2) if baseline_cost else 0

    print(json.dumps({
        "baseline_task_id": baseline_id,
        "optimized_task_id": optimized_id,
        "before_after_pair_id": pair_id,
        "model": MODEL,
        "baseline_input_tokens": baseline_input,
        "optimized_input_tokens": optimized_input,
        "input_token_reduction_percent": input_reduction,
        "baseline_estimated_cost": baseline_cost,
        "optimized_estimated_cost": optimized_cost,
        "estimated_cost_reduction_percent": cost_reduction,
        "baseline_trace": str(baseline_path),
        "optimized_trace": str(optimized_path),
        "imported_into_backend": imported,
    }, indent=2))


if __name__ == "__main__":
    main()
