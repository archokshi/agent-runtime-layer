import hashlib
import json
import re
from collections import defaultdict
from typing import Any

from app.analyzer.engine import analyze_events
from app.schemas import (
    ContextBlock,
    ContextOptimizationMetrics,
    ContextOptimizationReport,
    ContextOptimizationSavings,
    ContextOptimizationValidation,
    Event,
    OptimizedPromptPackage,
    Task,
)


STABLE_KINDS = ("system", "tool_schema", "repo_summary", "instruction", "prior_observation", "context_snapshot")
DYNAMIC_KINDS = ("latest", "tool_output", "error", "test", "patch", "diff", "model_output", "current")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def fingerprint(value: Any) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True)
    return f"sha256:{hashlib.sha256(normalize_text(value).encode('utf-8')).hexdigest()}"


def event_text(event: Event) -> str:
    for container in (event.attributes, event.payload):
        for key in ("context_hash", "prompt_hash", "fingerprint", "text", "content", "summary", "stdout_preview", "stderr_preview"):
            value = container.get(key)
            if value:
                return str(value)
    return json.dumps({"type": event.event_type, "name": event.name, "attributes": event.attributes}, sort_keys=True)


def event_tokens(event: Event) -> int:
    for key in ("size_tokens", "estimated_input_tokens", "input_tokens", "tokens", "reusable_tokens_estimate"):
        if key in event.attributes:
            return int(event.attributes.get(key) or 0)
    return 0


def block_kind(event: Event) -> str:
    kind = str(event.attributes.get("context_kind") or event.attributes.get("block_type") or event.name or event.event_type)
    return kind.lower()


def action_for_stable(kind: str) -> str:
    if "tool" in kind:
        return "lift_to_stable_prefix"
    if "repo" in kind:
        return "lift_to_stable_prefix"
    if "system" in kind:
        return "lift_to_stable_prefix"
    return "deduplicate_repeated_context"


def collect_context_blocks(events: list[Event]) -> tuple[list[ContextBlock], list[ContextBlock]]:
    candidates: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        if event.event_type not in {"context_snapshot", "model_call_start", "terminal_event", "error_event", "file_event"}:
            continue
        candidates[fingerprint(event_text(event))].append(event)

    stable_blocks: list[ContextBlock] = []
    dynamic_blocks: list[ContextBlock] = []
    for index, (block_fingerprint, grouped_events) in enumerate(candidates.items(), start=1):
        representative = grouped_events[-1]
        kind = block_kind(representative)
        tokens = max(event_tokens(event) for event in grouped_events)
        repeated_tokens = sum(int(event.attributes.get("repeated_tokens_estimate", 0)) for event in grouped_events)
        is_stable_kind = any(marker in kind for marker in STABLE_KINDS)
        is_dynamic_kind = any(marker in kind for marker in DYNAMIC_KINDS)
        is_repeated = len(grouped_events) > 1 or repeated_tokens > 0
        if is_repeated and is_stable_kind and not is_dynamic_kind:
            stable_blocks.append(
                ContextBlock(
                    block_id=f"stable_{index}",
                    type=kind,
                    fingerprint=block_fingerprint,
                    tokens=max(tokens, repeated_tokens),
                    occurrences=max(2, len(grouped_events)),
                    action=action_for_stable(kind),
                )
            )
        else:
            dynamic_blocks.append(
                ContextBlock(
                    block_id=f"dynamic_{index}",
                    type=kind,
                    fingerprint=block_fingerprint,
                    tokens=tokens,
                    occurrences=len(grouped_events),
                    action="keep_dynamic",
                )
            )
    if not dynamic_blocks:
        dynamic_blocks.append(
            ContextBlock(
                block_id="dynamic_current_instruction",
                type="current_instruction",
                fingerprint=fingerprint("current_instruction"),
                tokens=0,
                occurrences=1,
                action="keep_dynamic",
            )
        )
    return stable_blocks, dynamic_blocks


def optimize_context(task: Task, events: list[Event]) -> ContextOptimizationReport:
    report = analyze_events(task.task_id, events)
    stable_blocks, dynamic_blocks = collect_context_blocks(events)
    baseline_input_tokens = report.total_input_tokens or sum(event_tokens(event) for event in events if event.event_type == "context_snapshot")
    stable_tokens = min(sum(block.tokens for block in stable_blocks), baseline_input_tokens)
    optimized_input_tokens = max(0, baseline_input_tokens - stable_tokens)
    baseline_repeated_percent = report.repeated_context_percent
    optimized_repeated_tokens = max(0, report.repeated_context_tokens_estimate - stable_tokens)
    optimized_repeated_percent = round((optimized_repeated_tokens / optimized_input_tokens) * 100, 2) if optimized_input_tokens else 0.0
    baseline_cost = report.estimated_total_cost_dollars
    optimized_cost = round(baseline_cost * (optimized_input_tokens / baseline_input_tokens), 6) if baseline_input_tokens else baseline_cost
    input_reduction = round((stable_tokens / baseline_input_tokens) * 100, 2) if baseline_input_tokens else 0.0
    cost_reduction = round(((baseline_cost - optimized_cost) / baseline_cost) * 100, 2) if baseline_cost else input_reduction
    confidence = "high" if input_reduction >= 30 and stable_blocks else "medium" if stable_blocks else "low"
    return ContextOptimizationReport(
        task_id=task.task_id,
        baseline=ContextOptimizationMetrics(
            input_tokens=baseline_input_tokens,
            repeated_context_percent=baseline_repeated_percent,
            estimated_cost=baseline_cost,
        ),
        optimized=ContextOptimizationMetrics(
            input_tokens=optimized_input_tokens,
            repeated_context_percent=optimized_repeated_percent,
            estimated_cost=optimized_cost,
        ),
        savings=ContextOptimizationSavings(
            input_token_reduction_percent=input_reduction,
            estimated_cost_reduction_percent=cost_reduction,
            estimated_prefill_reduction_percent=input_reduction,
        ),
        stable_context_blocks=stable_blocks,
        dynamic_context_blocks=dynamic_blocks,
        optimized_prompt_package=OptimizedPromptPackage(
            stable_prefix_refs=[block.block_id for block in stable_blocks],
            dynamic_payload_refs=[block.block_id for block in dynamic_blocks],
            notes="Stable context is separated into prefix-cache-ready references. This does not claim actual KV-cache hits without backend measurement.",
        ),
        validation=ContextOptimizationValidation(
            task_success_preserved=task.task_success,
            confidence=confidence,
            next_validation_step="Run the same task through an SDK/coding-agent integration and compare measured token/cost impact.",
        ),
    )
