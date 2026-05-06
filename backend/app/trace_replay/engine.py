from datetime import datetime, timezone
from uuid import uuid4

from app.analyzer.engine import analyze_events
from app.schemas import (
    Event,
    HardwareAnalysisReport,
    SiliconBlueprintReport,
    Task,
    TraceReplayMetrics,
    TraceReplayReport,
    TraceReplayScenarioId,
    TraceReplayScenarioResult,
    TraceReplayDelta,
)


DEFAULT_SCENARIOS: list[TraceReplayScenarioId] = [
    "persistent_prefix_cache",
    "tool_wait_scheduler",
    "prefill_decode_split",
]


SCENARIO_NAMES: dict[TraceReplayScenarioId, tuple[str, str]] = {
    "persistent_prefix_cache": (
        "Persistent prefix cache",
        "Project impact if stable repeated prefixes are reused by a cache-aware backend.",
    ),
    "tool_wait_scheduler": (
        "Tool-wait scheduler",
        "Project impact if independent work is scheduled around blocking tool spans and idle gaps.",
    ),
    "prefill_decode_split": (
        "Prefill/decode split",
        "Project impact if input-heavy prefill work is isolated from decode-heavy execution.",
    ),
    "warm_context_tier": (
        "Warm context tier",
        "Project impact if repo summaries, tool schemas, and recent logs live in a reusable warm tier.",
    ),
    "kv_compression": (
        "KV/context compression",
        "Project impact if large reusable contexts are compressed before repeated prefill work.",
    ),
}


def _pct_reduction(before: float, after: float) -> float:
    if before <= 0:
        return 0.0
    return round(max(0.0, min(100.0, ((before - after) / before) * 100)), 2)


def _copy_metrics(metrics: TraceReplayMetrics, **updates) -> TraceReplayMetrics:
    data = metrics.model_dump()
    data.update(updates)
    return TraceReplayMetrics(**data)


def _delta(baseline: TraceReplayMetrics, projected: TraceReplayMetrics) -> TraceReplayDelta:
    return TraceReplayDelta(
        duration_reduction_percent=_pct_reduction(baseline.total_duration_ms, projected.total_duration_ms),
        input_token_reduction_percent=_pct_reduction(baseline.input_tokens, projected.input_tokens),
        estimated_cost_reduction_percent=_pct_reduction(baseline.estimated_cost_dollars, projected.estimated_cost_dollars),
        estimated_prefill_reduction_percent=_pct_reduction(baseline.estimated_prefill_ms, projected.estimated_prefill_ms),
        queue_pressure_reduction_percent=_pct_reduction(baseline.queue_pressure_score, projected.queue_pressure_score),
    )


def _baseline_metrics(
    tasks: list[Task],
    events_by_task: dict[str, list[Event]],
    hardware_reports: dict[str, HardwareAnalysisReport | None],
) -> TraceReplayMetrics:
    analyses = [analyze_events(task.task_id, events_by_task.get(task.task_id, [])) for task in tasks]
    total_duration = sum(report.total_task_duration_ms for report in analyses)
    model_time = sum(report.model_time_ms for report in analyses)
    tool_time = sum(report.tool_time_ms for report in analyses)
    idle_time = sum(report.orchestration_idle_ms for report in analyses)
    input_tokens = sum(report.total_input_tokens for report in analyses)
    output_tokens = sum(report.total_output_tokens for report in analyses)
    cost = round(sum(report.estimated_total_cost_dollars for report in analyses), 6)
    prefill_from_telemetry = sum(
        int((report.summary.avg_prefill_ms or 0) * report.summary.sample_count)
        for report in hardware_reports.values()
        if report is not None
    )
    estimated_prefill = prefill_from_telemetry or int(model_time * 0.65)
    queue_pressure = sum(
        float(report.summary.max_queue_depth or 0)
        for report in hardware_reports.values()
        if report is not None
    )
    return TraceReplayMetrics(
        total_duration_ms=total_duration,
        model_time_ms=model_time,
        tool_time_ms=tool_time,
        orchestration_idle_ms=idle_time,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_dollars=cost,
        estimated_prefill_ms=estimated_prefill,
        queue_pressure_score=round(queue_pressure, 2),
    )


def _scenario_result(
    scenario_id: TraceReplayScenarioId,
    baseline: TraceReplayMetrics,
    projected: TraceReplayMetrics,
    evidence: dict,
    confidence: float,
    confidence_reason: str,
    evidence_needed: list[str],
) -> TraceReplayScenarioResult:
    name, description = SCENARIO_NAMES[scenario_id]
    return TraceReplayScenarioResult(
        scenario_id=scenario_id,
        name=name,
        description=description,
        baseline=baseline,
        projected=projected,
        delta=_delta(baseline, projected),
        evidence=evidence,
        confidence=confidence,
        projection_confidence_reason=confidence_reason,
        requires_real_backend_validation=True,
        validation_evidence_needed=evidence_needed,
        notes="Projection only. This does not claim measured backend or hardware improvement.",
    )


def _comparison_summary(results: list[TraceReplayScenarioResult]) -> dict:
    if not results:
        return {}
    best_duration = max(results, key=lambda item: item.delta.duration_reduction_percent)
    best_cost = max(results, key=lambda item: item.delta.estimated_cost_reduction_percent)
    best_prefill = max(results, key=lambda item: item.delta.estimated_prefill_reduction_percent)
    return {
        "best_duration_scenario_id": best_duration.scenario_id,
        "best_duration_reduction_percent": best_duration.delta.duration_reduction_percent,
        "best_cost_scenario_id": best_cost.scenario_id,
        "best_cost_reduction_percent": best_cost.delta.estimated_cost_reduction_percent,
        "best_prefill_scenario_id": best_prefill.scenario_id,
        "best_prefill_reduction_percent": best_prefill.delta.estimated_prefill_reduction_percent,
        "scenario_count": len(results),
    }


def replay_blueprint(
    blueprint: SiliconBlueprintReport,
    tasks: list[Task],
    events_by_task: dict[str, list[Event]],
    hardware_reports: dict[str, HardwareAnalysisReport | None],
    scenario_ids: list[TraceReplayScenarioId] | None = None,
) -> TraceReplayReport:
    selected = scenario_ids or DEFAULT_SCENARIOS
    baseline = _baseline_metrics(tasks, events_by_task, hardware_reports)
    repeated_percent = blueprint.workload_profile.avg_repeated_context_percent
    cache_percent = blueprint.workload_profile.avg_cache_reuse_opportunity_percent
    bottlenecks = blueprint.bottleneck_map
    input_output_ratio = baseline.input_tokens / max(1, baseline.output_tokens)
    results: list[TraceReplayScenarioResult] = []

    if "persistent_prefix_cache" in selected:
        token_reduction = min(0.42, max(repeated_percent, cache_percent) / 100 * 0.7)
        prefill_reduction = min(0.38, token_reduction * 1.15)
        model_reduction = int(baseline.model_time_ms * prefill_reduction * 0.65)
        projected = _copy_metrics(
            baseline,
            total_duration_ms=max(0, baseline.total_duration_ms - model_reduction),
            model_time_ms=max(0, baseline.model_time_ms - model_reduction),
            input_tokens=int(baseline.input_tokens * (1 - token_reduction)),
            estimated_cost_dollars=round(baseline.estimated_cost_dollars * (1 - token_reduction * 0.8), 6),
            estimated_prefill_ms=int(baseline.estimated_prefill_ms * (1 - prefill_reduction)),
        )
        results.append(_scenario_result(
            "persistent_prefix_cache",
            baseline,
            projected,
            {"repeated_context_percent": repeated_percent, "cache_reuse_opportunity_percent": cache_percent},
            0.78 if repeated_percent or cache_percent else 0.45,
            "Confidence rises with repeated-context and cache-reuse evidence in the blueprint workload profile.",
            [
                "Run the same trace set on a prefix-cache-capable backend.",
                "Measure actual prefix/KV cache hit rate and prefill latency.",
                "Compare task success and token cost before and after cache-aware packaging.",
            ],
        ))

    if "tool_wait_scheduler" in selected:
        tool_reduction = 0.25 if bottlenecks.get("tool_wait", 0) else 0.1
        idle_reduction = 0.2 if baseline.orchestration_idle_ms else 0.0
        tool_saved = int(baseline.tool_time_ms * tool_reduction)
        idle_saved = int(baseline.orchestration_idle_ms * idle_reduction)
        projected = _copy_metrics(
            baseline,
            total_duration_ms=max(0, baseline.total_duration_ms - tool_saved - idle_saved),
            tool_time_ms=max(0, baseline.tool_time_ms - tool_saved),
            orchestration_idle_ms=max(0, baseline.orchestration_idle_ms - idle_saved),
            queue_pressure_score=round(baseline.queue_pressure_score * 0.85, 2),
        )
        results.append(_scenario_result(
            "tool_wait_scheduler",
            baseline,
            projected,
            {"tool_wait_bottleneck_count": bottlenecks.get("tool_wait", 0), "baseline_tool_time_ms": baseline.tool_time_ms},
            0.74,
            "Confidence is based on observed tool wait, idle time, and queue-pressure evidence.",
            [
                "Run a scheduler-enabled execution path on the same tasks.",
                "Measure wall-clock duration, idle gaps, and task success.",
                "Confirm independent tool/model work was actually overlapped.",
            ],
        ))

    if "prefill_decode_split" in selected:
        has_prefill_pressure = bottlenecks.get("prefill_bottleneck", 0) > 0 or input_output_ratio >= 8
        prefill_reduction = 0.28 if has_prefill_pressure else 0.12
        model_saved = int(baseline.model_time_ms * prefill_reduction * 0.55)
        projected = _copy_metrics(
            baseline,
            total_duration_ms=max(0, baseline.total_duration_ms - model_saved),
            model_time_ms=max(0, baseline.model_time_ms - model_saved),
            estimated_prefill_ms=int(baseline.estimated_prefill_ms * (1 - prefill_reduction)),
            queue_pressure_score=round(baseline.queue_pressure_score * 0.9, 2),
        )
        results.append(_scenario_result(
            "prefill_decode_split",
            baseline,
            projected,
            {"input_output_ratio": round(input_output_ratio, 2), "prefill_bottleneck_count": bottlenecks.get("prefill_bottleneck", 0)},
            0.72 if has_prefill_pressure else 0.52,
            "Confidence is based on input/output ratio and imported telemetry prefill bottleneck evidence.",
            [
                "Run on a backend that exposes separate prefill and decode timings.",
                "Measure TTFT, decode latency, queue depth, and throughput.",
                "Compare against the same prompts without prefill/decode separation.",
            ],
        ))

    if "warm_context_tier" in selected:
        token_reduction = min(0.25, repeated_percent / 100 * 0.45)
        projected = _copy_metrics(
            baseline,
            input_tokens=int(baseline.input_tokens * (1 - token_reduction)),
            estimated_cost_dollars=round(baseline.estimated_cost_dollars * (1 - token_reduction * 0.7), 6),
            estimated_prefill_ms=int(baseline.estimated_prefill_ms * (1 - token_reduction)),
        )
        results.append(_scenario_result(
            "warm_context_tier",
            baseline,
            projected,
            {"repeated_context_percent": repeated_percent, "memory_pressure_count": bottlenecks.get("memory_pressure", 0)},
            0.68,
            "Confidence is based on repeated-context evidence and memory-pressure signals.",
            [
                "Materialize stable repo/tool context in a reusable warm tier.",
                "Measure prompt assembly time, input tokens, and task success.",
                "Verify warm context lookup does not serve stale context.",
            ],
        ))

    if "kv_compression" in selected:
        compression_reduction = 0.16 if baseline.input_tokens >= 30000 else 0.07
        projected = _copy_metrics(
            baseline,
            input_tokens=int(baseline.input_tokens * (1 - compression_reduction)),
            estimated_cost_dollars=round(baseline.estimated_cost_dollars * (1 - compression_reduction * 0.45), 6),
            estimated_prefill_ms=int(baseline.estimated_prefill_ms * (1 - compression_reduction * 0.6)),
        )
        results.append(_scenario_result(
            "kv_compression",
            baseline,
            projected,
            {"input_tokens": baseline.input_tokens, "memory_pressure_count": bottlenecks.get("memory_pressure", 0)},
            0.58,
            "Confidence is lower because compression quality depends on backend and prompt semantics.",
            [
                "Run controlled compression/decompression experiments on repeated context blocks.",
                "Measure token reduction, latency, and answer quality.",
                "Validate task success does not regress.",
            ],
        ))

    best = max(results, key=lambda item: item.delta.duration_reduction_percent, default=None)
    return TraceReplayReport(
        replay_id=f"replay_{uuid4().hex[:12]}",
        blueprint_id=blueprint.blueprint_id,
        scenario_selection=selected,
        scenario_results=results,
        best_scenario_id=best.scenario_id if best else None,
        comparison_summary=_comparison_summary(results),
        aggregate_notes=[
            "Trace replay is deterministic and rule-based.",
            "Projected improvements are based on stored trace metrics and imported telemetry.",
            "Use measured backend runs later to validate or recalibrate these projections.",
            "v4.5 adds scenario selection, confidence reasons, and explicit validation evidence requirements.",
        ],
        limitations=[
            "No real KV-cache control is performed.",
            "No live backend routing or scheduler is performed.",
            "No hardware simulation, RTL, ASIC design, or watt-dollar measurement is performed.",
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
