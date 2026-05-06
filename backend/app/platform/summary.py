from datetime import datetime, timezone
from sqlite3 import Connection

from app.benchmarking import summarize_benchmark_runs
from app.schemas import (
    PlatformMetricCard,
    PlatformModuleCoverage,
    PlatformReadinessItem,
    PlatformRunbookStep,
    PlatformSummary,
)
from app.storage.repositories import list_benchmark_suite_runs, list_measured_validation_experiments


def _count(conn: Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _latest_id(conn: Connection, table: str, id_column: str) -> str | None:
    row = conn.execute(f"SELECT {id_column} FROM {table} ORDER BY created_at DESC LIMIT 1").fetchone()
    return row[0] if row else None


def _status(count: int) -> str:
    return "complete" if count > 0 else "missing"


def _readiness(score: int) -> str:
    if score >= 75:
        return "ready"
    if score >= 35:
        return "partial"
    return "missing"


def _percent(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((part / total) * 100)


def build_platform_summary(conn: Connection) -> PlatformSummary:
    task_count = _count(conn, "SELECT COUNT(*) FROM tasks")
    event_count = _count(conn, "SELECT COUNT(*) FROM events")
    analysis_count = _count(conn, "SELECT COUNT(*) FROM analysis_reports")
    optimization_count = _count(conn, "SELECT COUNT(*) FROM context_optimization_reports")
    scheduler_count = _count(conn, "SELECT COUNT(*) FROM scheduler_reports")
    backend_hint_count = _count(conn, "SELECT COUNT(*) FROM backend_hint_reports")
    telemetry_task_count = _count(conn, "SELECT COUNT(DISTINCT task_id) FROM hardware_telemetry_samples")
    hardware_analysis_count = _count(conn, "SELECT COUNT(*) FROM hardware_analysis_reports")
    blueprint_count = _count(conn, "SELECT COUNT(*) FROM silicon_blueprint_reports")
    replay_count = _count(conn, "SELECT COUNT(*) FROM trace_replay_reports")
    measured_experiment_count = _count(conn, "SELECT COUNT(*) FROM measured_validation_experiments")
    benchmark_run_count = _count(conn, "SELECT COUNT(*) FROM benchmark_suite_runs")
    model_call_count = _count(conn, "SELECT COUNT(*) FROM events WHERE event_type = 'model_call_start'")
    tool_call_count = _count(conn, "SELECT COUNT(*) FROM events WHERE event_type = 'tool_call_start'")
    validation_task_count = _count(conn, "SELECT COUNT(*) FROM tasks WHERE task_success IS NOT NULL OR benchmark_name IS NOT NULL")
    benchmark_summary = summarize_benchmark_runs(list_benchmark_suite_runs(conn))
    latest_blueprint_id = _latest_id(conn, "silicon_blueprint_reports", "blueprint_id")
    latest_replay_id = _latest_id(conn, "trace_replay_reports", "replay_id")

    trace_coverage = _percent(analysis_count, task_count)
    telemetry_coverage = _percent(telemetry_task_count, task_count)
    optimization_coverage = _percent(optimization_count, task_count)
    scheduler_coverage = _percent(scheduler_count, task_count)
    backend_coverage = _percent(backend_hint_count, task_count)

    readiness = [
        PlatformReadinessItem(
            category="Optimization",
            score=min(100, 35 + optimization_coverage),
            status=_readiness(min(100, 35 + optimization_coverage)),
            rationale=f"{optimization_count} task(s) have optimization executor reports out of {task_count}.",
            next_step="Run Optimize Context on high-token or repeated-context tasks.",
        ),
        PlatformReadinessItem(
            category="Backend Validation",
            score=min(100, 25 + backend_coverage + (20 if replay_count else 0)),
            status=_readiness(min(100, 25 + backend_coverage + (20 if replay_count else 0))),
            rationale=f"{backend_hint_count} task(s) have backend hints and {replay_count} replay report(s) exist.",
            next_step="Run measured backend experiments for the highest-confidence replay scenarios.",
        ),
        PlatformReadinessItem(
            category="Hardware-Aware Analysis",
            score=min(100, 20 + telemetry_coverage + (20 if hardware_analysis_count else 0)),
            status=_readiness(min(100, 20 + telemetry_coverage + (20 if hardware_analysis_count else 0))),
            rationale=f"{telemetry_task_count} task(s) have imported telemetry; {hardware_analysis_count} hardware analysis report(s) exist.",
            next_step="Import telemetry for more real agent tasks before broad hardware conclusions.",
        ),
        PlatformReadinessItem(
            category="Silicon Blueprint",
            score=90 if blueprint_count and replay_count else 70 if blueprint_count else 20,
            status=_readiness(90 if blueprint_count and replay_count else 70 if blueprint_count else 20),
            rationale=f"{blueprint_count} blueprint report(s) and {replay_count} replay report(s) exist.",
            next_step="Use the latest blueprint and replay report as the current architecture evidence artifact.",
        ),
        PlatformReadinessItem(
            category="Measured Benchmark Work",
            score=min(100, 20 + validation_task_count * 8 + measured_experiment_count * 15 + benchmark_run_count * 12),
            status=_readiness(min(100, 20 + validation_task_count * 8 + measured_experiment_count * 15 + benchmark_run_count * 12)),
            rationale=f"{validation_task_count} task(s) include validation metadata, {measured_experiment_count} measured experiment(s), and {benchmark_run_count} benchmark suite run(s) exist.",
            next_step="Add official SWE-bench/Aider/OpenHands runs after smoke records are stable.",
        ),
    ]

    runbook = [
        PlatformRunbookStep(
            step_id="trace",
            label="Import or capture traces",
            status="complete" if task_count and event_count else "missing",
            evidence=f"{task_count} task(s), {event_count} event(s).",
            next_step="Capture more real coding-agent traces.",
        ),
        PlatformRunbookStep(
            step_id="analyze",
            label="Analyze traces",
            status="complete" if analysis_count else "missing",
            evidence=f"{analysis_count} analysis report(s).",
            next_step="Import traces through the API/CLI so analysis is generated.",
        ),
        PlatformRunbookStep(
            step_id="optimize",
            label="Optimize repeated context",
            status="complete" if optimization_count else "partial" if task_count else "missing",
            evidence=f"{optimization_count} optimization report(s).",
            next_step="Run context optimization on repeated-context tasks.",
        ),
        PlatformRunbookStep(
            step_id="schedule",
            label="Run scheduler simulation",
            status="complete" if scheduler_count else "partial" if task_count else "missing",
            evidence=f"{scheduler_count} scheduler report(s).",
            next_step="Run scheduler simulation on tool-wait-heavy tasks.",
        ),
        PlatformRunbookStep(
            step_id="backend",
            label="Generate backend hints",
            status="complete" if backend_hint_count else "partial" if task_count else "missing",
            evidence=f"{backend_hint_count} backend hint report(s).",
            next_step="Generate backend hints for model-heavy traces.",
        ),
        PlatformRunbookStep(
            step_id="telemetry",
            label="Import hardware telemetry",
            status="complete" if telemetry_task_count else "partial" if task_count else "missing",
            evidence=f"{telemetry_task_count} task(s) with telemetry.",
            next_step="Import backend/GPU telemetry JSON for real runs.",
        ),
        PlatformRunbookStep(
            step_id="blueprint",
            label="Generate Silicon Blueprint",
            status="complete" if blueprint_count else "partial" if task_count else "missing",
            evidence=f"{blueprint_count} blueprint report(s).",
            next_step="Generate a blueprint from the local corpus.",
        ),
        PlatformRunbookStep(
            step_id="replay",
            label="Replay architecture scenarios",
            status="complete" if replay_count else "partial" if blueprint_count else "missing",
            evidence=f"{replay_count} replay report(s).",
            next_step="Run replay against the latest blueprint.",
        ),
    ]

    module_coverage = [
        PlatformModuleCoverage(module="Traces", status=_status(task_count), count=task_count, description="Imported or captured agent tasks."),
        PlatformModuleCoverage(module="Analysis", status=_status(analysis_count), count=analysis_count, description="Deterministic analyzer reports."),
        PlatformModuleCoverage(module="Optimization", status=_status(optimization_count), count=optimization_count, description="Context optimization executor reports."),
        PlatformModuleCoverage(module="Scheduler", status=_status(scheduler_count), count=scheduler_count, description="Runtime scheduler simulations."),
        PlatformModuleCoverage(module="Backend Hints", status=_status(backend_hint_count), count=backend_hint_count, description="Backend-aware routing/cache hints."),
        PlatformModuleCoverage(module="Hardware Telemetry", status=_status(telemetry_task_count), count=telemetry_task_count, description="Tasks with imported hardware/backend telemetry."),
        PlatformModuleCoverage(module="Blueprints", status=_status(blueprint_count), count=blueprint_count, description="Silicon Blueprint reports."),
        PlatformModuleCoverage(module="Replays", status=_status(replay_count), count=replay_count, description="Trace replay simulator reports."),
        PlatformModuleCoverage(module="Measured Validation", status=_status(measured_experiment_count), count=measured_experiment_count, description="Measured projected-vs-actual validation experiments."),
        PlatformModuleCoverage(module="Benchmark Suite", status=_status(benchmark_run_count), count=benchmark_run_count, description="SWE-bench, Aider, OpenHands, or custom coding-agent benchmark records."),
    ]

    return PlatformSummary(
        generated_at=datetime.now(timezone.utc).isoformat(),
        metrics=[
            PlatformMetricCard(label="Tasks", value=str(task_count), detail=f"{event_count} events"),
            PlatformMetricCard(label="Model Calls", value=str(model_call_count), detail=f"{tool_call_count} tool calls"),
            PlatformMetricCard(label="Trace Coverage", value=f"{trace_coverage}%", detail=f"{analysis_count} analyzed"),
            PlatformMetricCard(label="Telemetry Coverage", value=f"{telemetry_coverage}%", detail=f"{telemetry_task_count} task(s)"),
            PlatformMetricCard(label="Blueprints", value=str(blueprint_count), detail=latest_blueprint_id),
            PlatformMetricCard(label="Replays", value=str(replay_count), detail=latest_replay_id),
            PlatformMetricCard(label="Measured Experiments", value=str(measured_experiment_count), detail="projected vs actual"),
            PlatformMetricCard(label="Benchmark Runs", value=str(benchmark_run_count), detail=f"{benchmark_summary.task_count} task results"),
        ],
        module_coverage=module_coverage,
        readiness=readiness,
        runbook=runbook,
        measured_validation=list_measured_validation_experiments(conn)[:5],
        benchmark_suite=benchmark_summary,
        latest_blueprint_id=latest_blueprint_id,
        latest_replay_id=latest_replay_id,
        limitations=[
            "v5.0 is a local platform overview, not a cloud SaaS.",
            "No production auth, billing, multi-tenant controls, real backend control, or hardware simulation are implemented.",
            "Readiness scores are deterministic local heuristics and should be calibrated with real benchmark results.",
        ],
    )
