from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from app.analyzer.engine import analyze_events
from app.schemas import (
    BlueprintArchitectureRecommendation,
    Event,
    HardwareAnalysisReport,
    HardwarePrimitiveScore,
    SiliconBlueprintReport,
    SiliconBlueprintValidationSummary,
    Task,
    WorkloadProfile,
)


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _priority(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def generate_silicon_blueprint(
    name: str,
    tasks: list[Task],
    events_by_task: dict[str, list[Event]],
    hardware_reports: dict[str, HardwareAnalysisReport | None],
) -> SiliconBlueprintReport:
    analyses = [analyze_events(task.task_id, events_by_task.get(task.task_id, [])) for task in tasks]
    bottlenecks = Counter(report.bottleneck_category for report in analyses)
    hardware_bottlenecks = Counter(
        bottleneck.category
        for report in hardware_reports.values()
        if report is not None
        for bottleneck in report.bottlenecks
    )
    total_input = sum(report.total_input_tokens for report in analyses)
    total_output = sum(report.total_output_tokens for report in analyses)
    repeated_avg = _avg([report.repeated_context_percent for report in analyses])
    cache_avg = _avg([report.cache_reuse_opportunity_percent for report in analyses])
    tool_wait_ms = sum(report.tool_time_ms for report in analyses)
    model_time_ms = sum(report.model_time_ms for report in analyses)
    idle_ms = sum(report.orchestration_idle_ms for report in analyses)
    retry_count = sum(report.retry_count for report in analyses)
    prefill_pressure = hardware_bottlenecks.get("prefill_bottleneck", 0)
    cache_pressure = hardware_bottlenecks.get("cache_miss_pressure", 0)
    memory_pressure = hardware_bottlenecks.get("memory_pressure", 0)
    queue_pressure = hardware_bottlenecks.get("queue_saturation", 0)
    telemetry_task_count = sum(1 for report in hardware_reports.values() if report is not None and report.summary.sample_count > 0)

    memory_recs: list[BlueprintArchitectureRecommendation] = []
    if repeated_avg >= 20 or cache_avg >= 20 or cache_pressure:
        score = min(95, max(repeated_avg, cache_avg) + cache_pressure * 20)
        memory_recs.append(BlueprintArchitectureRecommendation(
            recommendation_id="memory:persistent-prefix-kv",
            category="memory_hierarchy",
            title="Persistent prefix/KV reuse tier",
            rationale="Traces show repeated context and/or low cache hit rates, making reusable prefix storage a high-value memory hierarchy primitive.",
            priority=_priority(score),  # type: ignore[arg-type]
            confidence=min(0.94, 0.55 + score / 100),
            metrics={"avg_repeated_context_percent": repeated_avg, "avg_cache_reuse_opportunity_percent": cache_avg, "cache_pressure_traces": cache_pressure},
        ))
    if total_input >= 30000 or memory_pressure:
        score = min(90, total_input / 1000 + memory_pressure * 25)
        memory_recs.append(BlueprintArchitectureRecommendation(
            recommendation_id="memory:warm-context-tier",
            category="memory_hierarchy",
            title="Warm context memory tier",
            rationale="Large context volume or GPU memory pressure suggests value in a warm tier for repo summaries, tool schemas, and recent logs.",
            priority=_priority(score),  # type: ignore[arg-type]
            confidence=min(0.88, 0.5 + score / 120),
            metrics={"total_input_tokens": total_input, "memory_pressure_traces": memory_pressure},
        ))

    primitive_scores = [
        HardwarePrimitiveScore(
            primitive="persistent_kv_cache",
            score=round(min(100, repeated_avg + cache_avg + cache_pressure * 20), 2),
            rationale="Useful when prompts share stable prefixes and cache hit rates are low.",
            evidence={"avg_repeated_context_percent": repeated_avg, "avg_cache_reuse_opportunity_percent": cache_avg, "cache_pressure_traces": cache_pressure},
        ),
        HardwarePrimitiveScore(
            primitive="prefix_matching",
            score=round(min(100, repeated_avg * 1.4 + cache_avg), 2),
            rationale="Useful for finding reusable prompt/context prefixes before dispatch.",
            evidence={"avg_repeated_context_percent": repeated_avg, "avg_cache_reuse_opportunity_percent": cache_avg},
        ),
        HardwarePrimitiveScore(
            primitive="prefill_decode_split",
            score=round(min(100, (total_input / max(1, total_output)) * 5 + prefill_pressure * 25), 2),
            rationale="Useful when input-heavy workloads or telemetry show prefill-dominated backend time.",
            evidence={"total_input_tokens": total_input, "total_output_tokens": total_output, "prefill_pressure_traces": prefill_pressure},
        ),
        HardwarePrimitiveScore(
            primitive="tool_wait_scheduler",
            score=round(min(100, (tool_wait_ms / max(1, model_time_ms + tool_wait_ms + idle_ms)) * 100 + queue_pressure * 10), 2),
            rationale="Useful when tool spans, queues, or idle gaps dominate end-to-end agent time.",
            evidence={"tool_wait_ms": tool_wait_ms, "idle_ms": idle_ms, "queue_pressure_traces": queue_pressure},
        ),
        HardwarePrimitiveScore(
            primitive="retry_checkpointing",
            score=round(min(100, retry_count * 20), 2),
            rationale="Useful when repeated attempts can reuse intermediate state or branch from known-good checkpoints.",
            evidence={"retry_count": retry_count},
        ),
    ]
    primitive_scores.sort(key=lambda item: item.score, reverse=True)

    runtime_recs: list[BlueprintArchitectureRecommendation] = []
    if tool_wait_ms > 0 or queue_pressure:
        runtime_recs.append(BlueprintArchitectureRecommendation(
            recommendation_id="runtime:queue-aware-scheduler",
            category="runtime",
            title="Queue-aware tool/model scheduler",
            rationale="Trace and telemetry evidence shows blocking tool wait, idle time, or backend queue pressure.",
            priority=_priority(min(100, queue_pressure * 25 + tool_wait_ms / 1000)),  # type: ignore[arg-type]
            confidence=0.76,
            metrics={"tool_wait_ms": tool_wait_ms, "idle_ms": idle_ms, "queue_pressure_traces": queue_pressure},
        ))
    if repeated_avg >= 20 or cache_pressure:
        runtime_recs.append(BlueprintArchitectureRecommendation(
            recommendation_id="runtime:cache-local-routing",
            category="runtime",
            title="Cache-local request routing",
            rationale="Repeated context and cache miss pressure indicate routing should preserve prefix locality once real backend integration exists.",
            priority=_priority(min(100, repeated_avg + cache_pressure * 20)),  # type: ignore[arg-type]
            confidence=0.8,
            metrics={"avg_repeated_context_percent": repeated_avg, "cache_pressure_traces": cache_pressure},
        ))

    benchmark_proposals = [
        BlueprintArchitectureRecommendation(
            recommendation_id="benchmark:repeated-context-suite",
            category="benchmark",
            title="Repeated-context coding-agent suite",
            rationale="Measure prefix reuse, prefill cost, cache hit rate, and task success across repeated repo/tool context workloads.",
            priority="high" if repeated_avg >= 20 else "medium",
            confidence=0.82,
            metrics={"avg_repeated_context_percent": repeated_avg},
        ),
        BlueprintArchitectureRecommendation(
            recommendation_id="benchmark:hardware-telemetry-suite",
            category="benchmark",
            title="Telemetry-correlated backend suite",
            rationale="Pair task traces with imported backend telemetry to validate queue, memory, cache, prefill, and decode claims.",
            priority="high" if hardware_bottlenecks else "medium",
            confidence=0.78,
            metrics={"hardware_bottleneck_counts": dict(hardware_bottlenecks)},
        ),
    ]

    return SiliconBlueprintReport(
        blueprint_id=f"blueprint_{uuid4().hex[:12]}",
        name=name,
        task_ids=[task.task_id for task in tasks],
        workload_profile=WorkloadProfile(
            task_count=len(tasks),
            model_call_count=sum(report.model_call_count for report in analyses),
            tool_call_count=sum(report.tool_call_count for report in analyses),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cost_dollars=round(sum(report.estimated_total_cost_dollars for report in analyses), 6),
            avg_repeated_context_percent=repeated_avg,
            avg_cache_reuse_opportunity_percent=cache_avg,
            bottleneck_counts=dict(bottlenecks + hardware_bottlenecks),
        ),
        bottleneck_map=dict(bottlenecks + hardware_bottlenecks),
        memory_hierarchy_recommendations=memory_recs,
        hardware_primitive_rankings=primitive_scores,
        backend_runtime_recommendations=runtime_recs,
        benchmark_proposals=benchmark_proposals,
        validation_summary=SiliconBlueprintValidationSummary(
            local_trace_count=len(tasks),
            target_progress_percent=round(min(100, (len(tasks) / 100) * 100), 2),
            tasks_with_hardware_telemetry=telemetry_task_count,
            real_world_validation_status="partial_local_corpus" if len(tasks) < 100 else "target_trace_count_met",
            remaining_validation_items=[
                "Run the report on 100+ real agent traces before claiming broad workload coverage.",
                "Add more official benchmark traces, such as SWE-bench Lite or Verified tasks.",
                "Calibrate primitive scores with human review after more real traces are available.",
            ],
        ),
        limitations=[
            "Rule-based architecture report only.",
            "Not ASIC design, RTL, FPGA, or hardware simulation.",
            "Confidence depends on trace and imported telemetry coverage.",
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
