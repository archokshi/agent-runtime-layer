from collections import Counter
from dataclasses import dataclass, field

from app.schemas import BenchmarkSuiteMetrics, BenchmarkSuiteRun, BenchmarkSuiteRunCreate, BenchmarkSuiteSummary, Task


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def _optional_percent(values: list[bool | None]) -> float | None:
    known = [value for value in values if value is not None]
    if not known:
        return None
    return _percent(sum(1 for value in known if value), len(known))


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


@dataclass
class BenchmarkValidationReport:
    task_result_count: int = 0
    before_after_pairs: list[str] = field(default_factory=list)


def build_benchmark_validation_report(runs: list[BenchmarkSuiteRun], tasks: list[Task]) -> BenchmarkValidationReport:
    task_result_count = sum(run.metrics.task_count for run in runs)
    pair_ids: set[str] = set()
    for task in tasks:
        if task.before_after_pair_id:
            pair_ids.add(task.before_after_pair_id)
    return BenchmarkValidationReport(task_result_count=task_result_count, before_after_pairs=list(pair_ids))
