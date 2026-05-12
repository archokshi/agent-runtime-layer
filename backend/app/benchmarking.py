from collections import Counter
from datetime import UTC, datetime

from app.schemas import (
    BenchmarkBeforeAfterPair,
    BenchmarkSuiteMetrics,
    BenchmarkSuiteRun,
    BenchmarkSuiteRunCreate,
    BenchmarkSuiteSummary,
    BenchmarkValidationReport,
    CorpusCoverageItem,
    Phase2EvidenceNeed,
    Task,
)


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def _optional_percent(values: list[bool | None]) -> float | None:
    known = [value for value in values if value is not None]
    if not known:
        return None
    return _percent(sum(1 for value in known if value), len(known))


def _status(count: int, target: int) -> str:
    if count <= 0:
        return "missing"
    if count >= target:
        return "ready"
    return "partial"


def calculate_benchmark_metrics(payload: BenchmarkSuiteRunCreate) -> BenchmarkSuiteMetrics:
    results = payload.task_results
    task_count = len(results)
    return BenchmarkSuiteMetrics(
        task_count=task_count,
        trace_completion_rate_percent=_percent(sum(1 for result in results if result.trace_complete), task_count),
        task_success_rate_percent=_optional_percent([result.task_success for result in results]),
        actionable_recommendation_rate_percent=_optional_percent(
            [result.actionable_recommendation for result in results]
        ),
        avg_retry_count=round(sum(result.retry_count for result in results) / task_count, 2) if task_count else 0.0,
        avg_duration_seconds=round(sum(result.duration_seconds for result in results) / task_count, 2) if task_count else 0.0,
        total_cost_dollars=round(sum(result.total_cost_dollars for result in results), 6),
    )


def build_benchmark_run(payload: BenchmarkSuiteRunCreate, created_at: str) -> BenchmarkSuiteRun:
    return BenchmarkSuiteRun(
        suite_name=payload.suite_name,
        suite_version=payload.suite_version,
        agent_name=payload.agent_name,
        agent_version=payload.agent_version,
        run_mode=payload.run_mode,
        source=payload.source,
        task_results=payload.task_results,
        metrics=calculate_benchmark_metrics(payload),
        limitations=payload.limitations,
        created_at=created_at,
    )


def summarize_benchmark_runs(runs: list[BenchmarkSuiteRun], limit: int = 5) -> BenchmarkSuiteSummary:
    task_count = sum(run.metrics.task_count for run in runs)
    trace_complete = sum(
        round(run.metrics.trace_completion_rate_percent * run.metrics.task_count / 100)
        for run in runs
    )
    success_known = 0
    success_true = 0
    recommendation_known = 0
    recommendation_true = 0
    suite_counts = Counter(run.suite_name for run in runs)

    for run in runs:
        for result in run.task_results:
            if result.task_success is not None:
                success_known += 1
                success_true += 1 if result.task_success else 0
            if result.actionable_recommendation is not None:
                recommendation_known += 1
                recommendation_true += 1 if result.actionable_recommendation else 0

    return BenchmarkSuiteSummary(
        run_count=len(runs),
        task_count=task_count,
        suite_counts=dict(suite_counts),
        trace_completion_rate_percent=_percent(trace_complete, task_count),
        task_success_rate_percent=_percent(success_true, success_known) if success_known else None,
        actionable_recommendation_rate_percent=_percent(recommendation_true, recommendation_known)
        if recommendation_known
        else None,
        latest_runs=runs[:limit],
        limitations=[
            "Benchmark records are imported/local evidence unless run_mode is official.",
            "This layer does not download SWE-bench, install OpenHands, or execute external benchmark harnesses automatically.",
            "Do not claim broad benchmark performance from smoke or dry-run records.",
        ],
    )


def build_benchmark_validation_report(runs: list[BenchmarkSuiteRun], tasks: list[Task]) -> BenchmarkValidationReport:
    task_result_count = sum(run.metrics.task_count for run in runs)
    trace_complete_count = sum(1 for run in runs for result in run.task_results if result.trace_complete)
    success_known_count = sum(1 for run in runs for result in run.task_results if result.task_success is not None)
    actionable_count = sum(
        1 for run in runs for result in run.task_results if result.actionable_recommendation is True
    )
    official_task_count = sum(run.metrics.task_count for run in runs if run.run_mode == "official")
    local_or_imported_task_count = task_result_count - official_task_count
    suite_counts = Counter(run.suite_name for run in runs)
    mode_counts = Counter(run.run_mode for run in runs)

    pair_tasks: dict[str, list[Task]] = {}
    for task in tasks:
        if task.before_after_pair_id:
            pair_tasks.setdefault(task.before_after_pair_id, []).append(task)

    before_after_pairs: list[BenchmarkBeforeAfterPair] = []
    for pair_id, paired_tasks in sorted(pair_tasks.items()):
        baseline = next((task for task in paired_tasks if task.baseline_or_optimized == "baseline"), None)
        optimized = next((task for task in paired_tasks if task.baseline_or_optimized == "optimized"), None)
        baseline_success = baseline.task_success if baseline else None
        optimized_success = optimized.task_success if optimized else None
        success_preserved = (
            baseline_success is True and optimized_success is True
            if baseline_success is not None and optimized_success is not None
            else None
        )
        before_after_pairs.append(
            BenchmarkBeforeAfterPair(
                before_after_pair_id=pair_id,
                baseline_task_id=baseline.task_id if baseline else None,
                optimized_task_id=optimized.task_id if optimized else None,
                baseline_success=baseline_success,
                optimized_success=optimized_success,
                success_preserved=success_preserved,
                evidence="Linked baseline/optimized task metadata from local trace corpus.",
            )
        )

    suite_coverage = [
        CorpusCoverageItem(
            category=suite,
            count=count,
            percent=_percent(count, len(runs)),
            target=None,
            status="ready" if count else "missing",
            phase2_consumes="Repeatable benchmark slice for backend/system/hardware comparison.",
            next_step="Link benchmark records to imported traces and outcome metadata.",
        )
        for suite, count in sorted(suite_counts.items())
    ]
    run_mode_coverage = [
        CorpusCoverageItem(
            category=mode,
            count=count,
            percent=_percent(count, len(runs)),
            target=None,
            status="ready" if mode == "official" and count else "partial" if count else "missing",
            phase2_consumes="Truth label separating official benchmark evidence from local smoke/imported records.",
            next_step="Only mark official after running the external benchmark harness.",
        )
        for mode, count in sorted(mode_counts.items())
    ]
    outcome_coverage = [
        CorpusCoverageItem(
            category="Task outcomes",
            count=success_known_count,
            percent=_percent(success_known_count, task_result_count),
            target=task_result_count or None,
            status=_status(success_known_count, max(task_result_count, 1)),
            phase2_consumes="Correctness boundary for comparing faster or cheaper agent runs.",
            next_step="Attach task_success, tests passed/failed, patch generation, and retry metadata.",
        ),
        CorpusCoverageItem(
            category="Actionable recommendations",
            count=actionable_count,
            percent=_percent(actionable_count, task_result_count),
            target=task_result_count or None,
            status=_status(actionable_count, max(task_result_count, 1)),
            phase2_consumes="Shows whether traces produce useful optimization candidates.",
            next_step="Review recommendation evidence and confidence for each benchmark trace.",
        ),
    ]
    trace_completion = CorpusCoverageItem(
        category="Trace completion",
        count=trace_complete_count,
        percent=_percent(trace_complete_count, task_result_count),
        target=task_result_count or None,
        status=_status(trace_complete_count, max(task_result_count, 1)),
        phase2_consumes="Determines whether benchmark tasks include enough trace evidence for workload modeling.",
        next_step="Ensure benchmark traces include task lifecycle, model/tool/file/terminal/context events.",
    )

    readiness_score = min(
        100,
        round(_percent(trace_complete_count, task_result_count) * 0.30)
        + round(_percent(success_known_count, task_result_count) * 0.20)
        + round(_percent(actionable_count, task_result_count) * 0.15)
        + min(20, task_result_count * 2)
        + (15 if official_task_count else 0),
    )
    readiness_status = "ready" if readiness_score >= 80 and task_result_count >= 25 else "partial" if readiness_score else "missing"

    return BenchmarkValidationReport(
        generated_at=datetime.now(UTC).isoformat(),
        run_count=len(runs),
        task_result_count=task_result_count,
        official_task_count=official_task_count,
        local_or_imported_task_count=local_or_imported_task_count,
        suite_coverage=suite_coverage,
        run_mode_coverage=run_mode_coverage,
        outcome_coverage=outcome_coverage,
        trace_completion=trace_completion,
        before_after_pairs=before_after_pairs,
        phase2_evidence_value=[
            Phase2EvidenceNeed(
                need_id="repeatable_benchmark_slices",
                label="Repeatable Benchmark Slices",
                status=readiness_status,  # type: ignore[arg-type]
                evidence=f"{task_result_count} benchmark task result(s) across {len(runs)} run(s).",
                source="benchmark_suite_runs table",
                phase2_use="Feeds backend/system/hardware comparisons with repeatable workload slices.",
                next_step="Increase to 10-25 linked benchmark-style traces before stronger Phase 2 claims.",
            ),
            Phase2EvidenceNeed(
                need_id="official_benchmark_evidence",
                label="Official Benchmark Evidence",
                status="ready" if official_task_count else "missing",
                evidence=f"{official_task_count} official benchmark task result(s).",
                source="benchmark run_mode",
                phase2_use="Separates public benchmark claims from local smoke/imported validation records.",
                next_step="Run the external benchmark harness before marking any run official.",
            ),
        ],
        readiness_score=readiness_score,
        readiness_status=readiness_status,  # type: ignore[arg-type]
        limitations=[
            "Benchmark validation summarizes imported/local records unless run_mode is official.",
            "Smoke, dry-run, and imported records are useful evidence but not public benchmark claims.",
            "Benchmark records do not prove real KV-cache hits or hardware speedup.",
        ],
        next_steps=[
            "Link benchmark records to full task traces with outcome metadata.",
            "Run 10-25 benchmark-style coding-agent tasks for Phase 2 backend/system comparison.",
            "Add official benchmark harness output only when externally executed and reproducible.",
        ],
    )
