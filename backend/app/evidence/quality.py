from datetime import UTC, datetime
from sqlite3 import Connection

from app.analyzer.engine import analyze_events
from app.schemas import EvidenceQualityCategory, EvidenceQualityMetric, EvidenceQualityReport
from app.storage.repositories import (
    list_all_hardware_telemetry_samples,
    list_benchmark_suite_runs,
    list_events,
    list_measured_validation_experiments,
    list_tasks,
)


QUALITY_POINTS = {
    "measured": 100,
    "estimated": 60,
    "inferred": 40,
    "missing": 0,
}


def _count(conn: Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _quality(has_measured: bool = False, has_estimate: bool = False, has_inference: bool = False) -> str:
    if has_measured:
        return "measured"
    if has_estimate:
        return "estimated"
    if has_inference:
        return "inferred"
    return "missing"


def _metric(
    metric_id: str,
    label: str,
    value: str,
    quality: str,
    source: str,
    phase2_use: str,
    risk_if_overclaimed: str,
    next_validation_step: str,
) -> EvidenceQualityMetric:
    return EvidenceQualityMetric(
        metric_id=metric_id,
        label=label,
        value=value,
        quality=quality,
        source=source,
        phase2_use=phase2_use,
        risk_if_overclaimed=risk_if_overclaimed,
        next_validation_step=next_validation_step,
    )


def _category(category: str, metrics: list[EvidenceQualityMetric]) -> EvidenceQualityCategory:
    measured = sum(1 for metric in metrics if metric.quality == "measured")
    estimated = sum(1 for metric in metrics if metric.quality == "estimated")
    inferred = sum(1 for metric in metrics if metric.quality == "inferred")
    missing = sum(1 for metric in metrics if metric.quality == "missing")
    score = round(sum(QUALITY_POINTS[metric.quality] for metric in metrics) / len(metrics)) if metrics else 0
    status = "ready" if score >= 80 else "partial" if score > 0 else "missing"
    return EvidenceQualityCategory(
        category=category,
        measured_count=measured,
        estimated_count=estimated,
        inferred_count=inferred,
        missing_count=missing,
        score=score,
        status=status,
        metrics=metrics,
    )


def build_evidence_quality_report(conn: Connection) -> EvidenceQualityReport:
    tasks = list_tasks(conn)
    events_by_task = {task.task_id: list_events(conn, task.task_id) for task in tasks}
    analyses = [analyze_events(task.task_id, events_by_task[task.task_id]) for task in tasks]
    samples = list_all_hardware_telemetry_samples(conn)
    benchmark_runs = list_benchmark_suite_runs(conn)
    measured_experiments = list_measured_validation_experiments(conn)

    task_count = len(tasks)
    event_count = sum(len(events) for events in events_by_task.values())
    model_events = sum(1 for events in events_by_task.values() for event in events if event.event_type == "model_call_start")
    tool_events = sum(1 for events in events_by_task.values() for event in events if event.event_type == "tool_call_start")
    context_events = sum(1 for events in events_by_task.values() for event in events if event.event_type == "context_snapshot")
    tasks_with_outcomes = sum(
        1
        for task in tasks
        if task.task_success is not None or task.tests_passed is not None or task.tests_failed is not None
    )
    total_cost = round(sum(report.estimated_total_cost_dollars for report in analyses), 6)
    repeated_context_avg = round(
        sum(report.repeated_context_percent for report in analyses) / len(analyses), 2
    ) if analyses else 0.0
    official_tasks = sum(run.metrics.task_count for run in benchmark_runs if run.run_mode == "official")
    benchmark_task_results = sum(run.metrics.task_count for run in benchmark_runs)

    telemetry_tasks = {sample.task_id for sample in samples}
    gpu_samples = sum(1 for sample in samples if sample.gpu_utilization_percent is not None)
    cpu_samples = sum(1 for sample in samples if sample.cpu_utilization_percent is not None)
    memory_samples = sum(1 for sample in samples if sample.gpu_memory_used_percent is not None)
    queue_samples = sum(1 for sample in samples if sample.queue_depth is not None)
    prefill_decode_samples = sum(1 for sample in samples if sample.prefill_ms is not None and sample.decode_ms is not None)
    cache_samples = sum(1 for sample in samples if sample.kv_cache_hit_rate is not None)
    hardware_speedup_records = 0

    trace_metrics = [
        _metric(
            "trace_count",
            "Trace count",
            str(task_count),
            _quality(has_measured=task_count > 0),
            "SQLite tasks table",
            "Corpus volume for workload representativeness.",
            "A tiny corpus can look representative when it is only a demo sample.",
            "Capture 100+ real coding-agent traces.",
        ),
        _metric(
            "event_count",
            "Event count",
            str(event_count),
            _quality(has_measured=event_count > 0),
            "SQLite events table",
            "Execution graph shape and agent loop structure.",
            "Sparse events can hide actual model/tool/orchestration behavior.",
            "Require task lifecycle, model, tool, file, terminal, and context events.",
        ),
        _metric(
            "model_tool_spans",
            "Model/tool spans",
            f"{model_events} model / {tool_events} tool",
            _quality(has_measured=model_events > 0 and tool_events > 0),
            "Trace event types",
            "Model/tool/I/O/CPU split for utilization-collapse analysis.",
            "Without spans, model time and tool wait become guesswork.",
            "Instrument real coding agents with model and tool spans.",
        ),
        _metric(
            "context_snapshots",
            "Context snapshots",
            str(context_events),
            _quality(has_measured=context_events > 0),
            "context_snapshot events",
            "Context lifetime and prefix/KV reuse opportunity.",
            "Repeated-context claims can become hand-wavy without context hashes/tokens.",
            "Log context snapshots with token counts and stable/dynamic labels.",
        ),
    ]

    optimization_metrics = [
        _metric(
            "model_cost",
            "Model cost",
            f"${total_cost:.6f}",
            _quality(has_estimate=total_cost > 0),
            "Analyzer token/cost metadata",
            "Cost pressure and optimization prioritization.",
            "Estimated cost can be mistaken for billed provider cost.",
            "Import measured provider usage/cost where available.",
        ),
        _metric(
            "repeated_context",
            "Repeated context",
            f"{repeated_context_avg}%",
            _quality(has_estimate=repeated_context_avg > 0),
            "Analyzer context snapshot estimates",
            "Persistent prefix/cache opportunity and memory hierarchy signal.",
            "Repeated-token estimates are not real KV-cache hits.",
            "Compare against backend cache hit/miss telemetry.",
        ),
        _metric(
            "before_after_validation",
            "Measured before/after validation",
            str(len(measured_experiments)),
            _quality(has_measured=bool(measured_experiments)),
            "measured_validation_experiments table",
            "Evidence that optimization preserves success while reducing tokens/cost/time.",
            "Optimization recommendations can look valuable without outcome preservation.",
            "Run controlled baseline/optimized experiments with success metadata.",
        ),
    ]

    benchmark_metrics = [
        _metric(
            "benchmark_task_results",
            "Benchmark task results",
            str(benchmark_task_results),
            _quality(has_measured=benchmark_task_results > 0),
            "benchmark_suite_runs table",
            "Repeatable workload slices for backend/system/hardware comparison.",
            "Smoke records can be mistaken for broad benchmark validity.",
            "Add linked SWE-bench/Aider/OpenHands/custom benchmark traces.",
        ),
        _metric(
            "official_benchmark_results",
            "Official benchmark results",
            str(official_tasks),
            _quality(has_measured=official_tasks > 0),
            "benchmark run_mode=official",
            "High-confidence public benchmark evidence.",
            "Calling local smoke records official would destroy credibility.",
            "Only mark official after running the external benchmark harness.",
        ),
        _metric(
            "task_outcomes",
            "Task outcomes",
            f"{tasks_with_outcomes}/{task_count}",
            _quality(has_measured=tasks_with_outcomes > 0),
            "Task validation metadata",
            "Correctness and success-preservation boundaries.",
            "Speed/cost improvements without correctness are not useful.",
            "Attach task_success, tests, patch, retry, and files changed metadata.",
        ),
    ]

    telemetry_metrics = [
        _metric(
            "gpu_utilization",
            "GPU utilization",
            f"{gpu_samples} sample(s)",
            _quality(has_measured=gpu_samples > 0),
            "Imported backend/system/hardware telemetry",
            "Tests GPU underutilization in agent loops.",
            "Without telemetry, GPU utilization claims are speculation.",
            "Import GPU utilization from real backend runs.",
        ),
        _metric(
            "cpu_utilization",
            "CPU utilization",
            f"{cpu_samples} sample(s)",
            _quality(has_measured=cpu_samples > 0),
            "Imported backend/system/hardware telemetry",
            "CPU orchestration pressure and scheduler gap analysis.",
            "CPU bottlenecks can be missed if only GPU metrics are tracked.",
            "Import CPU/orchestrator utilization metrics.",
        ),
        _metric(
            "memory_pressure",
            "Memory pressure",
            f"{memory_samples} sample(s)",
            _quality(has_measured=memory_samples > 0),
            "Imported backend/system/hardware telemetry",
            "HBM/DRAM/CXL/warm-context memory hierarchy signal.",
            "Memory architecture recommendations need measured pressure.",
            "Record memory usage during context-heavy traces.",
        ),
        _metric(
            "queue_depth",
            "Queue depth",
            f"{queue_samples} sample(s)",
            _quality(has_measured=queue_samples > 0),
            "Imported backend/system telemetry",
            "Backend scheduling, queueing, and routing gap analysis.",
            "Queue saturation can be confused with model slowness.",
            "Import backend queue depth during each trace.",
        ),
        _metric(
            "prefill_decode_timing",
            "Prefill/decode timing",
            f"{prefill_decode_samples} sample(s)",
            _quality(has_measured=prefill_decode_samples > 0),
            "Imported backend/system telemetry",
            "Prefill/decode split for architecture and backend choices.",
            "Without split timing, all model latency looks the same.",
            "Import prefill_ms and decode_ms from serving backend.",
        ),
        _metric(
            "kv_cache_hit_rate",
            "KV/cache hit rate",
            f"{cache_samples} sample(s)",
            _quality(has_measured=cache_samples > 0),
            "Imported backend/system telemetry",
            "Validates real cache reuse from repeated context.",
            "Repeated context opportunity is not the same as a backend cache hit.",
            "Import actual KV/cache hit and miss telemetry.",
        ),
        _metric(
            "hardware_speedup",
            "Measured hardware speedup",
            str(hardware_speedup_records),
            "missing",
            "No measured hardware experiment table",
            "Only needed later for backend/system/hardware speedup claims.",
            "Claiming speedup without measurement would overstate Phase 1.",
            "Run controlled backend/system/hardware experiments in Phase 2 or later.",
        ),
    ]

    categories = [
        _category("Trace Evidence", trace_metrics),
        _category("Optimization Evidence", optimization_metrics),
        _category("Benchmark Evidence", benchmark_metrics),
        _category("Backend/System Telemetry Evidence", telemetry_metrics),
    ]
    overall_score = round(sum(category.score for category in categories) / len(categories)) if categories else 0
    overall_status = "ready" if overall_score >= 80 else "partial" if overall_score > 0 else "missing"
    missing_evidence = [
        metric.label
        for category in categories
        for metric in category.metrics
        if metric.quality == "missing"
    ]

    return EvidenceQualityReport(
        generated_at=datetime.now(UTC).isoformat(),
        overall_score=overall_score,
        overall_status=overall_status,
        categories=categories,
        missing_evidence=missing_evidence,
        phase2_safety_rules=[
            "Phase 2 may use measured metrics as primary architecture evidence.",
            "Phase 2 may use estimated metrics only as hypotheses that require validation.",
            "Phase 2 may use inferred metrics only to prioritize instrumentation gaps.",
            "Phase 2 must not use missing metrics as evidence for architecture decisions.",
            "Repeated-context opportunity must not be described as a real KV-cache hit unless backend/system telemetry measures it.",
            "No hardware speedup, utilization improvement, or silicon claim is allowed without measured backend/system/hardware experiments.",
        ],
        limitations=[
            "Evidence quality is deterministic local scoring, not external certification.",
            "Measured means stored or imported in local data; it does not imply benchmark officiality unless run_mode is official.",
            "Estimated and inferred metrics are useful for direction, but not for final hardware claims.",
        ],
        next_steps=[
            "Turn missing high-value metrics into instrumentation tasks before Phase 2 decisions.",
            "Import backend/system telemetry for GPU, CPU, memory, queue, prefill/decode, cache, and fabric/network symptoms where available.",
            "Add official benchmark records only after running external benchmark harnesses.",
            "Use the evidence quality report as a gate before architecture recommendations.",
        ],
    )
