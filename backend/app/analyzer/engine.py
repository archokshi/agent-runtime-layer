from datetime import datetime
from typing import Any

from app.schemas import (
    AnalysisReport,
    BlueprintPreview,
    BlueprintRecommendation,
    Event,
    OptimizationRecommendation,
    OptimizationReport,
    Task,
    ValidationComparison,
    ValidationReport,
)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_from_bounds(events: list[Event]) -> int:
    if not events:
        return 0
    start = parse_ts(events[0].timestamp)
    end = parse_ts(events[-1].timestamp)
    return max(0, int((end - start).total_seconds() * 1000))


def paired_span_durations(events: list[Event], start_type: str, end_type: str) -> int:
    starts: dict[str, datetime] = {}
    total = 0
    for event in events:
        if event.event_type == start_type:
            starts[event.span_id] = parse_ts(event.timestamp)
        elif event.event_type == end_type:
            explicit = event.attributes.get("latency_ms")
            if isinstance(explicit, int | float):
                total += int(explicit)
            elif event.span_id in starts:
                total += max(0, int((parse_ts(event.timestamp) - starts[event.span_id]).total_seconds() * 1000))
    return total


def count_retries(events: list[Event]) -> int:
    failed_tools: dict[str, int] = {}
    retry_count = 0
    for event in events:
        if event.event_type == "tool_call_end" and event.attributes.get("status") == "failed":
            failed_tools[event.name.replace("_end", "")] = failed_tools.get(event.name.replace("_end", ""), 0) + 1
        if event.event_type == "error_event" and event.attributes.get("recoverable") is True:
            retry_count += 1
    return retry_count + sum(max(0, count - 1) for count in failed_tools.values())


def classify_bottleneck(report: dict[str, Any]) -> str:
    duration = max(1, report["total_task_duration_ms"])
    repeated_percent = report["repeated_context_percent"]
    tool_ratio = report["tool_time_ms"] / duration
    model_ratio = report["model_time_ms"] / duration
    idle_ratio = report["orchestration_idle_ms"] / duration
    if report["retry_count"] >= 2:
        return "retry_loop"
    if repeated_percent >= 35:
        return "repeated_context"
    if tool_ratio >= 0.45:
        return "tool_wait"
    if model_ratio >= 0.45:
        return "model_latency"
    if idle_ratio >= 0.35:
        return "orchestration_idle"
    if repeated_percent >= 20 and model_ratio >= 0.3:
        return "context_growth"
    return "mixed"


def analyze_events(task_id: str, events: list[Event]) -> AnalysisReport:
    sorted_events = sorted(events, key=lambda event: event.timestamp)
    total_duration = duration_from_bounds(sorted_events)
    model_time = paired_span_durations(sorted_events, "model_call_start", "model_call_end")
    tool_time = paired_span_durations(sorted_events, "tool_call_start", "tool_call_end")
    model_call_count = sum(1 for event in sorted_events if event.event_type == "model_call_start")
    tool_call_count = sum(1 for event in sorted_events if event.event_type == "tool_call_start")
    model_ends = [event for event in sorted_events if event.event_type == "model_call_end"]
    contexts = [event for event in sorted_events if event.event_type == "context_snapshot"]
    cache_events = [event for event in sorted_events if event.event_type == "cache_event"]

    # Primary: read from model_call_end events (native tracing)
    total_input = sum(int(event.attributes.get("input_tokens", 0)) for event in model_ends)
    total_output = sum(int(event.attributes.get("output_tokens", 0)) for event in model_ends)
    total_cost = round(sum(float(event.attributes.get("cost_dollars", 0.0)) for event in model_ends), 6)

    # Fallback: read from task_end events (Claude Code / Codex hook integration)
    # These carry transcript-parsed totals when no model_call_end events exist
    if total_input == 0 and total_cost == 0.0:
        task_ends = [e for e in sorted_events if e.event_type == "task_end"]
        for e in task_ends:
            total_input  += int(e.attributes.get("total_input_tokens", 0))
            total_output += int(e.attributes.get("total_output_tokens", 0))
            total_cost   += float(e.attributes.get("estimated_cost_usd", 0.0))
            if model_call_count == 0:
                model_call_count += int(e.attributes.get("model_calls", 0))
            # Repeated context from cache_read tokens
            if repeated_tokens == 0:
                repeated_tokens += int(e.attributes.get("repeated_tokens", 0))
            if context_tokens == 0:
                context_tokens += int(e.attributes.get("total_context_tokens", 0))
        total_cost = round(total_cost, 6)
        repeated_percent = round((repeated_tokens / context_tokens) * 100, 2) if context_tokens else 0.0
    repeated_tokens = sum(int(event.attributes.get("repeated_tokens_estimate", 0)) for event in contexts)
    context_tokens = sum(int(event.attributes.get("size_tokens", 0)) for event in contexts)
    reusable_tokens = sum(int(event.attributes.get("reusable_tokens_estimate", 0)) for event in cache_events)
    repeated_percent = round((repeated_tokens / context_tokens) * 100, 2) if context_tokens else 0.0
    cache_percent = round((reusable_tokens / max(1, context_tokens)) * 100, 2) if context_tokens else 0.0
    idle = max(0, total_duration - model_time - tool_time)

    report = {
        "task_id": task_id,
        "total_task_duration_ms": total_duration,
        "model_time_ms": model_time,
        "tool_time_ms": tool_time,
        "orchestration_idle_ms": idle,
        "model_call_count": model_call_count,
        "tool_call_count": tool_call_count,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "estimated_total_cost_dollars": total_cost,
        "repeated_context_tokens_estimate": repeated_tokens,
        "repeated_context_percent": repeated_percent,
        "cache_reuse_opportunity_percent": cache_percent,
        "retry_count": count_retries(sorted_events),
        "bottleneck_category": "mixed",
    }
    report["bottleneck_category"] = classify_bottleneck(report)
    return AnalysisReport(**report)


def generate_blueprint(task_id: str, report: AnalysisReport) -> BlueprintPreview:
    recommendations: list[BlueprintRecommendation] = []
    if report.repeated_context_percent >= 25 or report.cache_reuse_opportunity_percent >= 25:
        recommendations.append(BlueprintRecommendation(
            recommendation_id=f"{task_id}:prefix-cache",
            category="memory_hierarchy",
            title="Persistent KV/prefix cache recommended",
            rationale="The trace repeats a large share of context tokens, making reusable prefix storage a strong candidate.",
            confidence=min(0.95, 0.55 + report.repeated_context_percent / 100),
            metrics={"repeated_context_percent": report.repeated_context_percent, "cache_reuse_opportunity_percent": report.cache_reuse_opportunity_percent},
        ))
    if report.tool_time_ms > report.model_time_ms and report.tool_time_ms >= report.total_task_duration_ms * 0.35:
        recommendations.append(BlueprintRecommendation(
            recommendation_id=f"{task_id}:tool-scheduler",
            category="scheduler",
            title="Tool-wait-aware scheduler recommended",
            rationale="Tool execution dominates elapsed task time, so scheduling model work around blocking tools may reduce idle time.",
            confidence=0.78,
            metrics={"tool_time_ms": report.tool_time_ms, "model_time_ms": report.model_time_ms},
        ))
    if report.total_input_tokens >= 30000 or report.repeated_context_tokens_estimate >= 12000:
        recommendations.append(BlueprintRecommendation(
            recommendation_id=f"{task_id}:warm-context",
            category="memory_tier",
            title="Warm context tier recommended",
            rationale="Large context volume suggests benefit from a warm tier for repo summaries, tool schemas, and recent logs.",
            confidence=0.74,
            metrics={"total_input_tokens": report.total_input_tokens, "repeated_context_tokens_estimate": report.repeated_context_tokens_estimate},
        ))
    if report.model_time_ms >= 8000 and report.total_input_tokens > report.total_output_tokens * 10:
        recommendations.append(BlueprintRecommendation(
            recommendation_id=f"{task_id}:prefill-decode",
            category="inference_path",
            title="Prefill/decode split candidate",
            rationale="Input-heavy model calls indicate prefill cost may deserve separate capacity planning from decode.",
            confidence=0.7,
            metrics={"model_time_ms": report.model_time_ms, "total_input_tokens": report.total_input_tokens, "total_output_tokens": report.total_output_tokens},
        ))
    return BlueprintPreview(task_id=task_id, recommendations=recommendations)


def generate_optimization_recommendations(task_id: str, report: AnalysisReport) -> OptimizationReport:
    recommendations: list[OptimizationRecommendation] = []
    if report.repeated_context_percent >= 20:
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"{task_id}:opt-prefix-cache",
            category="context_caching",
            title="Cache repeated context prefixes",
            evidence=f"{report.repeated_context_percent:.1f}% of context tokens are repeated across snapshots.",
            action="Move stable repo summaries, tool schemas, and recurring instructions behind a reusable prefix/context cache.",
            estimated_time_savings_ms=int(report.model_time_ms * min(0.35, report.repeated_context_percent / 100)),
            estimated_cost_savings_dollars=round(report.estimated_total_cost_dollars * min(0.35, report.repeated_context_percent / 100), 6),
            confidence=min(0.92, 0.55 + report.repeated_context_percent / 100),
            metrics={
                "repeated_context_percent": report.repeated_context_percent,
                "repeated_context_tokens_estimate": report.repeated_context_tokens_estimate,
            },
        ))
    if report.tool_time_ms >= max(1000, report.total_task_duration_ms * 0.35):
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"{task_id}:opt-tool-wait",
            category="tool_scheduling",
            title="Reduce blocking tool wait",
            evidence=f"Tool execution consumed {report.tool_time_ms}ms of {report.total_task_duration_ms}ms total task time.",
            action="Batch independent terminal/file operations, run safe checks in parallel, and schedule model planning around long-running tools.",
            estimated_time_savings_ms=int(report.tool_time_ms * 0.25),
            estimated_cost_savings_dollars=0.0,
            confidence=0.78,
            metrics={"tool_time_ms": report.tool_time_ms, "tool_call_count": report.tool_call_count},
        ))
    if report.estimated_total_cost_dollars >= 0.01 and report.model_call_count >= 1:
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"{task_id}:opt-model-routing",
            category="model_routing",
            title="Route simple steps to smaller models",
            evidence=f"Model calls cost ${report.estimated_total_cost_dollars:.6f} for this task.",
            action="Keep large models for planning/edit decisions, but route summarization, validation parsing, and low-risk transformations to cheaper models.",
            estimated_time_savings_ms=0,
            estimated_cost_savings_dollars=round(report.estimated_total_cost_dollars * 0.2, 6),
            confidence=0.66,
            metrics={"model_call_count": report.model_call_count, "estimated_total_cost_dollars": report.estimated_total_cost_dollars},
        ))
    if report.retry_count >= 1:
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"{task_id}:opt-retries",
            category="retry_reduction",
            title="Reduce retry loops",
            evidence=f"The trace includes {report.retry_count} retry or recoverable failure signal(s).",
            action="Capture failing command output once, summarize the failure, and gate repeated attempts behind a changed hypothesis.",
            estimated_time_savings_ms=int((report.tool_time_ms + report.model_time_ms) * min(0.3, 0.1 * report.retry_count)),
            estimated_cost_savings_dollars=round(report.estimated_total_cost_dollars * min(0.3, 0.1 * report.retry_count), 6),
            confidence=0.72,
            metrics={"retry_count": report.retry_count},
        ))
    if report.orchestration_idle_ms >= max(1000, report.total_task_duration_ms * 0.25):
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"{task_id}:opt-idle",
            category="orchestration",
            title="Tighten orchestration idle time",
            evidence=f"Idle orchestration accounts for {report.orchestration_idle_ms}ms of elapsed task time.",
            action="Emit explicit spans around waiting states and move deterministic preparation work into those gaps.",
            estimated_time_savings_ms=int(report.orchestration_idle_ms * 0.3),
            estimated_cost_savings_dollars=0.0,
            confidence=0.62,
            metrics={"orchestration_idle_ms": report.orchestration_idle_ms},
        ))
    recommendations.sort(key=lambda rec: (rec.estimated_time_savings_ms, rec.estimated_cost_savings_dollars, rec.confidence), reverse=True)
    return OptimizationReport(task_id=task_id, recommendations=recommendations[:3])


def _percent_change(baseline: float, optimized: float) -> float | None:
    if baseline == 0:
        return None
    return round(((baseline - optimized) / baseline) * 100, 2)


def task_validation_metadata(task: Task, report: AnalysisReport) -> dict[str, Any]:
    return {
        "benchmark_name": task.benchmark_name,
        "benchmark_task_id": task.benchmark_task_id,
        "repo_name": task.repo_name,
        "issue_id": task.issue_id,
        "agent_name": task.agent_name,
        "baseline_or_optimized": task.baseline_or_optimized,
        "task_success": task.task_success,
        "tests_passed": task.tests_passed,
        "tests_failed": task.tests_failed,
        "patch_generated": task.patch_generated,
        "files_changed_count": task.files_changed_count,
        "retry_count": task.retry_count if task.retry_count is not None else report.retry_count,
        "before_after_pair_id": task.before_after_pair_id,
    }


def generate_validation_report(
    task: Task,
    report: AnalysisReport,
    paired_tasks: list[Task],
    paired_reports: dict[str, AnalysisReport],
) -> ValidationReport:
    comparison = None
    if task.before_after_pair_id:
        baseline = next((item for item in paired_tasks if item.baseline_or_optimized == "baseline"), None)
        optimized = next((item for item in paired_tasks if item.baseline_or_optimized == "optimized"), None)
        baseline_report = paired_reports.get(baseline.task_id) if baseline else None
        optimized_report = paired_reports.get(optimized.task_id) if optimized else None
        if baseline_report and optimized_report:
            comparison = ValidationComparison(
                before_after_pair_id=task.before_after_pair_id,
                baseline_task_id=baseline.task_id if baseline else None,
                optimized_task_id=optimized.task_id if optimized else None,
                repeated_input_token_reduction_percent=_percent_change(
                    baseline_report.repeated_context_tokens_estimate,
                    optimized_report.repeated_context_tokens_estimate,
                ),
                estimated_cost_reduction_percent=_percent_change(
                    baseline_report.estimated_total_cost_dollars,
                    optimized_report.estimated_total_cost_dollars,
                ),
                latency_change_percent=round(
                    ((optimized_report.total_task_duration_ms - baseline_report.total_task_duration_ms)
                     / baseline_report.total_task_duration_ms) * 100,
                    2,
                ) if baseline_report.total_task_duration_ms else None,
                success_preserved=bool(baseline.task_success and optimized.task_success) if baseline and optimized else None,
            )
    return ValidationReport(
        task_id=task.task_id,
        metadata=task_validation_metadata(task, report),
        comparison=comparison,
    )
