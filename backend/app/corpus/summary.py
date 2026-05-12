from collections import Counter
from datetime import UTC, datetime
from sqlite3 import Connection

from app.schemas import (
    CorpusCoverageItem,
    CorpusMetricCard,
    Phase2EvidenceNeed,
    TraceCorpusReport,
    TraceCorpusTaskSummary,
)
from app.storage.repositories import list_events, list_tasks


TARGET_TRACE_COUNT = 100


def _percent(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((count / total) * 100, 2)


def _status(count: int, total: int, ready_percent: float = 80.0) -> str:
    if total == 0 or count == 0:
        return "missing"
    if _percent(count, total) >= ready_percent:
        return "ready"
    return "partial"


def _volume_status(task_count: int) -> str:
    if task_count == 0:
        return "missing"
    if task_count >= TARGET_TRACE_COUNT:
        return "ready"
    return "partial"


def _quality_for_status(status: str) -> str:
    return "measured" if status in {"ready", "partial"} else "missing"


def _phase2_value(has_model: bool, has_tool: bool, has_context: bool, has_outcome: bool) -> str:
    values = []
    if has_model and has_tool:
        values.append("model/tool split")
    if has_context:
        values.append("context lifetime")
    if has_outcome:
        values.append("outcome distribution")
    if not values:
        return "basic execution evidence only"
    return ", ".join(values)


def build_trace_corpus_report(conn: Connection) -> TraceCorpusReport:
    tasks = list_tasks(conn)
    task_summaries: list[TraceCorpusTaskSummary] = []

    agents: Counter[str] = Counter()
    repos: Counter[str] = Counter()

    total_events = 0
    complete_traces = 0
    model_coverage = 0
    tool_coverage = 0
    file_coverage = 0
    terminal_coverage = 0
    context_coverage = 0
    outcome_coverage = 0
    retry_evidence = 0
    benchmark_coverage = 0

    for task in tasks:
        events = list_events(conn, task.task_id)
        event_types = {event.event_type for event in events}
        total_events += len(events)

        has_model = bool(event_types & {"model_call_start", "model_call_end"})
        has_tool = bool(event_types & {"tool_call_start", "tool_call_end"})
        has_file = "file_event" in event_types
        has_terminal = "terminal_event" in event_types
        has_context = "context_snapshot" in event_types
        has_outcome = any(
            value is not None
            for value in (
                task.task_success,
                task.tests_passed,
                task.tests_failed,
                task.patch_generated,
            )
        ) or task.status in {"completed", "failed"}
        has_retry = (task.retry_count or 0) > 0
        is_complete = "task_start" in event_types and "task_end" in event_types and len(events) >= 3

        complete_traces += int(is_complete)
        model_coverage += int(has_model)
        tool_coverage += int(has_tool)
        file_coverage += int(has_file)
        terminal_coverage += int(has_terminal)
        context_coverage += int(has_context)
        outcome_coverage += int(has_outcome)
        retry_evidence += int(has_retry)
        benchmark_coverage += int(task.benchmark_name is not None)

        agent_label = task.agent_name or task.agent_type or "unknown"
        agents[agent_label] += 1
        if task.repo_name:
            repos[task.repo_name] += 1

        task_summaries.append(
            TraceCorpusTaskSummary(
                task_id=task.task_id,
                goal=task.goal,
                agent_name=task.agent_name,
                agent_type=task.agent_type,
                repo_name=task.repo_name,
                benchmark_name=task.benchmark_name,
                event_count=len(events),
                has_model_events=has_model,
                has_tool_events=has_tool,
                has_file_events=has_file,
                has_terminal_events=has_terminal,
                has_context_snapshots=has_context,
                has_outcome_metadata=has_outcome,
                retry_count=task.retry_count,
                task_success=task.task_success,
                phase2_value=_phase2_value(has_model, has_tool, has_context, has_outcome),
            )
        )

    task_count = len(tasks)
    volume_percent = min(100.0, _percent(task_count, TARGET_TRACE_COUNT))
    graph_status = _status(complete_traces, task_count)
    split_status = _status(min(model_coverage, tool_coverage, max(file_coverage, terminal_coverage)), task_count)
    retry_status = _status(retry_evidence, task_count, ready_percent=20.0)
    context_status = _status(context_coverage, task_count)
    outcome_status = _status(outcome_coverage, task_count)
    benchmark_status = _status(benchmark_coverage, task_count, ready_percent=50.0)

    volume_score = min(35, round((task_count / TARGET_TRACE_COUNT) * 35))
    completeness_score = round(
        (
            _percent(complete_traces, task_count)
            + _percent(model_coverage, task_count)
            + _percent(tool_coverage, task_count)
            + _percent(context_coverage, task_count)
        )
        / 4
        * 0.25
    )
    outcome_score = round(_percent(outcome_coverage, task_count) * 0.15)
    diversity_score = min(15, (len(agents) * 5) + (len(repos) * 3))
    benchmark_score = round(_percent(benchmark_coverage, task_count) * 0.10)
    readiness_score = min(100, volume_score + completeness_score + outcome_score + diversity_score + benchmark_score)
    if task_count < 10:
        readiness_score = min(readiness_score, 30)
    elif task_count < TARGET_TRACE_COUNT:
        readiness_score = min(readiness_score, 70)
    readiness_status = "ready" if readiness_score >= 80 and task_count >= TARGET_TRACE_COUNT else _volume_status(task_count)

    coverage = [
        CorpusCoverageItem(
            category="Trace volume",
            count=task_count,
            percent=volume_percent,
            target=TARGET_TRACE_COUNT,
            status=_volume_status(task_count),
            phase2_consumes="Workload corpus size for Phase 2.0 workload modeling.",
            next_step="Capture more real coding-agent runs until the corpus reaches 100+ traces.",
        ),
        CorpusCoverageItem(
            category="Complete execution traces",
            count=complete_traces,
            percent=_percent(complete_traces, task_count),
            target=None,
            status=graph_status,
            phase2_consumes="Execution graph shape, span depth, and agent loop structure.",
            next_step="Ensure traces include task_start, task_end, and enough intermediate events.",
        ),
        CorpusCoverageItem(
            category="Model/tool/I/O split",
            count=min(model_coverage, tool_coverage, max(file_coverage, terminal_coverage)),
            percent=_percent(min(model_coverage, tool_coverage, max(file_coverage, terminal_coverage)), task_count),
            target=None,
            status=split_status,
            phase2_consumes="Bursty model calls, tool wait, CPU orchestration, and I/O split.",
            next_step="Capture model, tool, file, and terminal events from real agents.",
        ),
        CorpusCoverageItem(
            category="Context snapshots",
            count=context_coverage,
            percent=_percent(context_coverage, task_count),
            target=None,
            status=context_status,
            phase2_consumes="Context lifetime, repeated prefix state, and KV reuse opportunity.",
            next_step="Use SDK/adapters that log context_snapshot events with token metadata.",
        ),
        CorpusCoverageItem(
            category="Outcome metadata",
            count=outcome_coverage,
            percent=_percent(outcome_coverage, task_count),
            target=None,
            status=outcome_status,
            phase2_consumes="Success/failure distribution and optimization safety boundaries.",
            next_step="Attach tests passed/failed, patch generated, and task success metadata.",
        ),
        CorpusCoverageItem(
            category="Benchmark-linked traces",
            count=benchmark_coverage,
            percent=_percent(benchmark_coverage, task_count),
            target=None,
            status=benchmark_status,
            phase2_consumes="Repeatable workload slices for backend/hardware gap analysis.",
            next_step="Import SWE-bench/Aider/OpenHands/custom benchmark records when available.",
        ),
    ]

    phase2_evidence_needs = [
        Phase2EvidenceNeed(
            need_id="execution_graph_shapes",
            label="Execution Graph Shapes",
            status=graph_status,
            evidence=f"{complete_traces}/{task_count} traces include task lifecycle events.",
            phase2_use="Defines the agent loop graph that Phase 2.0 turns into a workload model.",
            next_step="Increase complete trace coverage and preserve parent span relationships.",
        ),
        Phase2EvidenceNeed(
            need_id="model_tool_cpu_io_split",
            label="Model / Tool / CPU / I/O Split",
            status=split_status,
            evidence=f"{model_coverage} model-covered, {tool_coverage} tool-covered, {file_coverage} file-covered, {terminal_coverage} terminal-covered traces.",
            phase2_use="Explains the GPU utilization collapse pattern from bursty model work and non-model waits.",
            next_step="Capture all four event families for representative coding-agent tasks.",
        ),
        Phase2EvidenceNeed(
            need_id="retry_backtrack_frequency",
            label="Retry And Backtrack Frequency",
            status=retry_status,
            evidence=f"{retry_evidence}/{task_count} traces currently include retry metadata.",
            phase2_use="Sizes checkpointing, branch rollback, and compiler/runtime recovery primitives.",
            next_step="Instrument retry loops, failed tests, backtracks, and branch boundaries.",
        ),
        Phase2EvidenceNeed(
            need_id="context_lifetime",
            label="Context Lifetime And Reuse",
            status=context_status,
            evidence=f"{context_coverage}/{task_count} traces include context snapshots.",
            phase2_use="Feeds persistent context, prefix/KV reuse, warm tier, and cache retention design.",
            next_step="Log stable/dynamic context snapshots with token counts and hashes.",
        ),
        Phase2EvidenceNeed(
            need_id="outcome_distribution",
            label="Outcome Distribution",
            status=outcome_status,
            evidence=f"{outcome_coverage}/{task_count} traces include task outcome metadata.",
            phase2_use="Prevents optimization and architecture recommendations from ignoring correctness.",
            next_step="Record task success, test outcomes, patch generation, and files changed.",
        ),
    ]

    limitations = [
        "Phase 1.1 is a corpus readiness report, not hardware validation.",
        "Readiness remains partial until the local corpus reaches 100+ representative real traces.",
        "Benchmark-linked records are evidence tracking unless marked as official externally executed runs.",
        "No real KV-cache hit, backend routing result, or hardware speedup is claimed from this report.",
    ]

    next_steps = [
        "Capture more real coding-agent traces with model/tool/file/terminal/context events.",
        "Attach outcome metadata so Phase 2 can separate faster runs from correct runs.",
        "Add benchmark-linked traces for repeatable backend and architecture comparisons.",
        "Import backend telemetry only when available from real systems.",
    ]

    metrics = [
        CorpusMetricCard(
            label="Trace corpus",
            value=f"{task_count}/{TARGET_TRACE_COUNT}",
            detail=f"{volume_percent}% of Phase 2 evidence target.",
            quality=_quality_for_status(_volume_status(task_count)),
        ),
        CorpusMetricCard(
            label="Events",
            value=str(total_events),
            detail="Stored trace events across the local corpus.",
            quality="measured" if total_events else "missing",
        ),
        CorpusMetricCard(
            label="Complete traces",
            value=f"{_percent(complete_traces, task_count)}%",
            detail=f"{complete_traces} traces include task lifecycle coverage.",
            quality=_quality_for_status(graph_status),
        ),
        CorpusMetricCard(
            label="Context coverage",
            value=f"{_percent(context_coverage, task_count)}%",
            detail="Traces with context snapshots for reuse/lifetime analysis.",
            quality=_quality_for_status(context_status),
        ),
        CorpusMetricCard(
            label="Outcome coverage",
            value=f"{_percent(outcome_coverage, task_count)}%",
            detail="Traces with success/failure or test outcome metadata.",
            quality=_quality_for_status(outcome_status),
        ),
        CorpusMetricCard(
            label="Readiness",
            value=f"{readiness_score}/100",
            detail=f"Status: {readiness_status}.",
            quality="inferred" if task_count else "missing",
        ),
    ]

    return TraceCorpusReport(
        generated_at=datetime.now(UTC).isoformat(),
        metrics=metrics,
        coverage=coverage,
        phase2_evidence_needs=phase2_evidence_needs,
        top_agents=dict(agents.most_common(5)),
        top_repos=dict(repos.most_common(5)),
        task_summaries=task_summaries,
        readiness_score=readiness_score,
        readiness_status=readiness_status,
        limitations=limitations,
        next_steps=next_steps,
    )
