from collections import Counter
from datetime import datetime, timezone
from sqlite3 import Connection

from app.analyzer.engine import analyze_events
from app.benchmarking import summarize_benchmark_runs
from app.schemas import (
    Phase1ArchitectureSignal,
    Phase1ExitPackage,
    Phase1Metric,
    Phase1Recommendation,
    Phase1TestPlanItem,
)
from app.storage.repositories import (
    list_benchmark_suite_runs,
    list_events,
    list_hardware_telemetry_samples,
    list_measured_validation_experiments,
    list_tasks,
)


def _count(conn: Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def _priority(score: int) -> str:
    if score >= 80:
        return "P0"
    if score >= 60:
        return "P1"
    if score >= 40:
        return "P2"
    return "P3"


def _recommendation(title: str, evidence: str, action: str, impact: int, confidence: int, effort: int, risk: int) -> Phase1Recommendation:
    score = max(0, min(100, impact + confidence + (100 - effort) // 2 - risk))
    return Phase1Recommendation(
        priority=_priority(score),  # type: ignore[arg-type]
        title=title,
        evidence=evidence,
        action=action,
        impact=impact,
        confidence=confidence,
        effort=effort,
        risk=risk,
        score=score,
    )


def generate_phase1_exit_package(conn: Connection) -> Phase1ExitPackage:
    tasks = list_tasks(conn)
    events_by_task = {task.task_id: list_events(conn, task.task_id) for task in tasks}
    analyses = [analyze_events(task.task_id, events_by_task[task.task_id]) for task in tasks]
    benchmark_summary = summarize_benchmark_runs(list_benchmark_suite_runs(conn))
    measured_experiments = list_measured_validation_experiments(conn)

    task_count = len(tasks)
    event_count = sum(len(events) for events in events_by_task.values())
    model_calls = sum(report.model_call_count for report in analyses)
    tool_calls = sum(report.tool_call_count for report in analyses)
    retries = sum(report.retry_count for report in analyses)
    total_duration_ms = sum(report.total_task_duration_ms for report in analyses)
    total_model_ms = sum(report.model_time_ms for report in analyses)
    total_tool_ms = sum(report.tool_time_ms for report in analyses)
    total_idle_ms = sum(report.orchestration_idle_ms for report in analyses)
    total_input = sum(report.total_input_tokens for report in analyses)
    total_output = sum(report.total_output_tokens for report in analyses)
    total_cost = round(sum(report.estimated_total_cost_dollars for report in analyses), 6)
    repeated_avg = _avg([report.repeated_context_percent for report in analyses])
    cache_avg = _avg([report.cache_reuse_opportunity_percent for report in analyses])
    bottlenecks = Counter(report.bottleneck_category for report in analyses)
    validation_tasks = [task for task in tasks if task.task_success is not None or task.benchmark_name]
    success_known = [task for task in tasks if task.task_success is not None]
    success_rate = _percent(sum(1 for task in success_known if task.task_success), len(success_known)) if success_known else None
    telemetry_task_count = _count(conn, "SELECT COUNT(DISTINCT task_id) FROM hardware_telemetry_samples")
    optimization_count = _count(conn, "SELECT COUNT(*) FROM context_optimization_reports")
    scheduler_count = _count(conn, "SELECT COUNT(*) FROM scheduler_reports")
    backend_hint_count = _count(conn, "SELECT COUNT(*) FROM backend_hint_reports")
    hardware_report_count = _count(conn, "SELECT COUNT(*) FROM hardware_analysis_reports")
    blueprint_count = _count(conn, "SELECT COUNT(*) FROM silicon_blueprint_reports")
    replay_count = _count(conn, "SELECT COUNT(*) FROM trace_replay_reports")
    telemetry_samples = sum(len(list_hardware_telemetry_samples(conn, task.task_id)) for task in tasks)

    recommendations = [
        _recommendation(
            "Separate stable and dynamic context",
            f"Average repeated context is {repeated_avg:.2f}% and cache reuse opportunity is {cache_avg:.2f}%.",
            "Use the v1.5 optimizer to generate prefix-cache-ready context packages for high-token tasks.",
            impact=85 if repeated_avg >= 25 else 60,
            confidence=85 if optimization_count else 65,
            effort=30,
            risk=10,
        ),
        _recommendation(
            "Test prefix-cache-capable backends",
            f"{backend_hint_count} backend hint report(s), {replay_count} replay report(s), and {benchmark_summary.task_count} benchmark task result(s) exist.",
            "Run a Phase 1.5 comparison across current backend, vLLM prefix caching, SGLang/RadixAttention-style serving, and Dynamo-style cache-aware routing where available.",
            impact=80 if cache_avg >= 20 else 55,
            confidence=70 if backend_hint_count else 45,
            effort=65,
            risk=20,
        ),
        _recommendation(
            "Evaluate tool-wait-aware scheduling",
            f"Tool time is {total_tool_ms}ms and orchestration idle time is {total_idle_ms}ms across the local corpus.",
            "Use Phase 1.5 workloads to compare baseline execution with scheduler-overlap strategies.",
            impact=75 if total_tool_ms > total_model_ms else 45,
            confidence=75 if scheduler_count else 50,
            effort=45,
            risk=15,
        ),
        _recommendation(
            "Add measured backend telemetry before hardware claims",
            f"{telemetry_task_count} of {task_count} task(s) have telemetry and {hardware_report_count} hardware analysis report(s) exist.",
            "Import backend/GPU telemetry for benchmark runs before making platform or silicon claims.",
            impact=70,
            confidence=80 if telemetry_task_count else 45,
            effort=55,
            risk=10,
        ),
        _recommendation(
            "Expand official benchmark coverage",
            f"Benchmark suite has {benchmark_summary.run_count} run(s) and {benchmark_summary.task_count} task result(s).",
            "Run a small official SWE-bench Lite/Verified smoke set, then expand only after trace completion is stable.",
            impact=65,
            confidence=60 if benchmark_summary.task_count else 35,
            effort=70,
            risk=15,
        ),
    ]
    recommendations.sort(key=lambda item: item.score, reverse=True)

    metric_quality = [
        Phase1Metric(name="Trace corpus", value=f"{task_count} task(s), {event_count} event(s)", evidence="Stored task and event rows.", quality="measured" if task_count else "missing"),
        Phase1Metric(name="Model/tool timing", value=f"{total_model_ms}ms model, {total_tool_ms}ms tool", evidence="Analyzer-derived span timing.", quality="estimated" if analyses else "missing"),
        Phase1Metric(name="Context reuse", value=f"{repeated_avg:.2f}% repeated, {cache_avg:.2f}% cache opportunity", evidence="Context snapshot and analyzer estimates.", quality="estimated" if analyses else "missing"),
        Phase1Metric(name="Benchmark evidence", value=f"{benchmark_summary.task_count} task result(s)", evidence="Imported benchmark suite records.", quality="measured" if benchmark_summary.task_count else "missing"),
        Phase1Metric(name="Outcome quality", value="unknown" if success_rate is None else f"{success_rate:.2f}% success", evidence="Task validation metadata.", quality="measured" if success_rate is not None else "missing"),
        Phase1Metric(name="Hardware symptoms", value=f"{telemetry_samples} telemetry sample(s)", evidence="Imported backend/hardware telemetry only.", quality="measured" if telemetry_samples else "missing"),
        Phase1Metric(name="Optimization validation", value=f"{len(measured_experiments)} measured experiment(s)", evidence="Projected-vs-measured validation records.", quality="measured" if measured_experiments else "missing"),
    ]
    readiness_inputs = [
        min(30, task_count * 3),
        15 if benchmark_summary.task_count else 0,
        15 if measured_experiments else 0,
        15 if telemetry_task_count else 0,
        10 if blueprint_count else 0,
        10 if replay_count else 0,
        5 if success_rate is not None else 0,
    ]
    readiness = min(100, sum(readiness_inputs))

    evaluation_package = {
        "workload_corpus_summary": {
            "task_count": task_count,
            "event_count": event_count,
            "benchmark_run_count": benchmark_summary.run_count,
            "benchmark_task_count": benchmark_summary.task_count,
            "validation_task_count": len(validation_tasks),
            "success_rate_percent": success_rate,
        },
        "agent_execution_profile": {
            "model_calls": model_calls,
            "tool_calls": tool_calls,
            "retry_count": retries,
            "avg_model_calls_per_task": _avg([report.model_call_count for report in analyses]),
            "avg_tool_calls_per_task": _avg([report.tool_call_count for report in analyses]),
            "bottleneck_counts": dict(bottlenecks),
        },
        "context_kv_reuse_profile": {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "avg_repeated_context_percent": repeated_avg,
            "avg_cache_reuse_opportunity_percent": cache_avg,
            "kv_cache_note": "Opportunity only; no real KV-cache control or backend KV-hit claim.",
        },
        "model_compute_profile": {
            "model_time_ms": total_model_ms,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "estimated_cost_dollars": total_cost,
        },
        "tool_io_orchestration_profile": {
            "tool_time_ms": total_tool_ms,
            "orchestration_idle_ms": total_idle_ms,
            "tool_wait_share_percent": _percent(total_tool_ms, max(1, total_duration_ms)),
            "idle_share_percent": _percent(total_idle_ms, max(1, total_duration_ms)),
        },
        "backend_hardware_symptom_profile": {
            "telemetry_task_count": telemetry_task_count,
            "hardware_analysis_report_count": hardware_report_count,
            "backend_hint_report_count": backend_hint_count,
            "telemetry_note": "Imported telemetry only; no live polling or hardware simulation.",
        },
        "outcome_quality_profile": {
            "known_success_task_count": len(success_known),
            "success_rate_percent": success_rate,
            "measured_experiment_count": len(measured_experiments),
            "benchmark_task_count": benchmark_summary.task_count,
        },
    }

    recommendation_package = {
        "executive_recommendation_summary": [item.title for item in recommendations[:5]],
        "prioritized_recommendations": [item.model_dump() for item in recommendations],
        "current_infrastructure_action_plan": [
            "Run Optimize Context on high repeated-context tasks.",
            "Use backend hints to select Phase 1.5 backend candidates.",
            "Import backend telemetry for benchmark and Aider/OpenHands traces.",
            "Record every benchmark run through the v0.5 benchmark suite API.",
        ],
    }

    hardware_tests = [
        Phase1TestPlanItem(
            platform="Current backend baseline",
            test="Run the same benchmark/coding-agent tasks without runtime optimization.",
            metrics=["task latency", "success rate", "cost/task", "trace completion"],
            success_criteria="Creates a clean baseline for every later backend comparison.",
        ),
        Phase1TestPlanItem(
            platform="vLLM prefix caching",
            test="Run repeated-context tasks with stable prefixes preserved.",
            metrics=["TTFT", "input tokens", "prefix/cache hit evidence", "cost/task"],
            success_criteria="Measured reduction in prompt/prefill work without success regression.",
        ),
        Phase1TestPlanItem(
            platform="SGLang/RadixAttention-style backend",
            test="Run multi-call agent traces with shared prefixes and branching/retry behavior.",
            metrics=["latency", "cache reuse", "retry loop cost", "success rate"],
            success_criteria="Improves repeated-context tasks versus current backend.",
        ),
        Phase1TestPlanItem(
            platform="Dynamo-style cache-aware routing",
            test="Replay backend-hint scenarios with cache-local routing where available.",
            metrics=["queue depth", "cache locality", "TTFT", "goodput"],
            success_criteria="Improves cache locality or queue behavior on agent traces.",
        ),
        Phase1TestPlanItem(
            platform="CPU/tool orchestration path",
            test="Profile repo search, file edits, test execution, and terminal wait.",
            metrics=["tool time", "idle time", "CPU utilization", "scheduler overlap"],
            success_criteria="Identifies whether orchestration/tool wait dominates hardware choices.",
        ),
    ]

    architecture_signals = [
        Phase1ArchitectureSignal(
            signal="Persistent prefix/KV memory",
            strength="strong" if repeated_avg >= 30 or cache_avg >= 30 else "medium" if repeated_avg >= 10 else "weak",
            evidence=f"Repeated context {repeated_avg:.2f}%, cache opportunity {cache_avg:.2f}%.",
            implication="Prioritize persistent prefix/KV reuse tests before any custom hardware direction.",
        ),
        Phase1ArchitectureSignal(
            signal="Warm context tier",
            strength="strong" if total_input >= 50000 else "medium" if total_input >= 10000 else "weak",
            evidence=f"Total input tokens across local corpus: {total_input}.",
            implication="Evaluate DRAM/CXL/NVMe-style warm context storage only if larger corpora preserve this signal.",
        ),
        Phase1ArchitectureSignal(
            signal="Tool-wait-aware scheduler",
            strength="strong" if total_tool_ms > total_model_ms else "medium" if total_tool_ms else "weak",
            evidence=f"Tool time {total_tool_ms}ms vs model time {total_model_ms}ms.",
            implication="Treat scheduling as a system/runtime primitive before silicon.",
        ),
        Phase1ArchitectureSignal(
            signal="Hardware telemetry readiness",
            strength="medium" if telemetry_task_count else "missing",
            evidence=f"{telemetry_task_count} task(s) have imported telemetry.",
            implication="Phase 1.5 should add real backend telemetry before Phase 2 makes hardware claims.",
        ),
    ]

    return Phase1ExitPackage(
        generated_at=datetime.now(timezone.utc).isoformat(),
        workload_evaluation_package=evaluation_package,
        workload_recommendation_package=recommendation_package,
        metric_quality_scorecard=metric_quality,
        architecture_readiness_score=readiness,
        architecture_readiness_rationale=(
            "Ready for Phase 1.5 smoke evaluation." if readiness >= 60
            else "Partial evidence; collect more benchmark and telemetry records before broad hardware conclusions."
        ),
        phase_1_5_hardware_test_plan=hardware_tests,
        phase_2_architecture_signals=architecture_signals,
        do_not_do_yet=[
            "Do not claim official SWE-bench/OpenHands performance from smoke or imported records.",
            "Do not claim real KV-cache hits unless measured from a backend.",
            "Do not build hardware simulation, RTL, FPGA, ASIC, or chip artifacts in Phase 1.011.",
            "Do not choose a silicon product before Phase 1.5 existing-platform tests.",
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def render_phase1_exit_markdown(report: Phase1ExitPackage) -> str:
    lines = [
        "# Phase 1.011 Workload Evaluation + Recommendation Package",
        "",
        f"- Package ID: `{report.package_id}`",
        f"- Version: `{report.package_version}`",
        f"- Mode: `{report.mode}`",
        f"- Generated: `{report.generated_at}`",
        f"- Architecture readiness: {report.architecture_readiness_score}/100",
        f"- Readiness rationale: {report.architecture_readiness_rationale}",
        "",
        "## Workload Evaluation Package",
        "",
    ]
    for section, values in report.workload_evaluation_package.items():
        lines.extend([f"### {section.replace('_', ' ').title()}", ""])
        if isinstance(values, dict):
            lines.extend(f"- {key.replace('_', ' ')}: {value}" for key, value in values.items())
        else:
            lines.append(str(values))
        lines.append("")
    lines.extend(["## Metric Quality Scorecard", ""])
    lines.extend(f"- **{metric.name}** ({metric.quality}): {metric.value}. {metric.evidence}" for metric in report.metric_quality_scorecard)
    lines.extend(["", "## Workload Recommendation Package", ""])
    for item in report.workload_recommendation_package.get("prioritized_recommendations", []):
        lines.append(f"- **{item['priority']} {item['title']}** score {item['score']}: {item['action']} Evidence: {item['evidence']}")
    lines.extend(["", "## Phase 1.5 Existing Hardware Test Plan", ""])
    lines.extend(f"- **{item.platform}**: {item.test} Success: {item.success_criteria}" for item in report.phase_1_5_hardware_test_plan)
    lines.extend(["", "## Phase 2 Architecture Signals", ""])
    lines.extend(f"- **{item.signal}** ({item.strength}): {item.evidence} Implication: {item.implication}" for item in report.phase_2_architecture_signals)
    lines.extend(["", "## Do Not Do Yet", ""])
    lines.extend(f"- {item}" for item in report.do_not_do_yet)
    return "\n".join(lines) + "\n"
