from datetime import UTC, datetime
from sqlite3 import Connection

from app.benchmarking import build_benchmark_validation_report
from app.corpus.summary import build_trace_corpus_report
from app.evidence.quality import build_evidence_quality_report
from app.phase2_handoff.engine import generate_phase2_handoff_package
from app.schemas import EvidenceCampaignReport, EvidenceCampaignTarget, EvidenceCampaignTrack, Phase2HandoffPackage
from app.storage.repositories import (
    list_benchmark_suite_runs,
    list_tasks,
    save_phase2_handoff_package,
)
from app.telemetry.summary import build_telemetry_corpus_report


def _percent(current: int, target: int) -> float:
    if target <= 0:
        return 100.0
    return round(min(100.0, (current / target) * 100), 2)


def _status(current: int, target: int) -> str:
    if current >= target:
        return "ready"
    if current > 0:
        return "partial"
    return "missing"


def _target(
    target_id: str,
    label: str,
    current: int,
    target: int,
    phase2_use: str,
    next_step: str,
) -> EvidenceCampaignTarget:
    return EvidenceCampaignTarget(
        target_id=target_id,
        label=label,
        current=current,
        target=target,
        percent=_percent(current, target),
        status=_status(current, target),  # type: ignore[arg-type]
        phase2_use=phase2_use,
        next_step=next_step,
    )


def _track_status(targets: list[EvidenceCampaignTarget]) -> str:
    if targets and all(target.status == "ready" for target in targets):
        return "ready"
    if any(target.current > 0 for target in targets):
        return "partial"
    return "missing"


def _track(
    track_id: str,
    name: str,
    summary: str,
    targets: list[EvidenceCampaignTarget],
    phase2_consumes: list[str],
    missing_items: list[str],
    next_steps: list[str],
) -> EvidenceCampaignTrack:
    return EvidenceCampaignTrack(
        track_id=track_id,
        name=name,
        summary=summary,
        status=_track_status(targets),  # type: ignore[arg-type]
        targets=targets,
        phase2_consumes=phase2_consumes,
        missing_items=missing_items,
        next_steps=next_steps,
    )


def _required_trace_count(corpus) -> int:
    return sum(
        1
        for task in corpus.task_summaries
        if task.has_model_events
        and task.has_tool_events
        and task.has_file_events
        and task.has_terminal_events
        and task.has_context_snapshots
        and task.has_outcome_metadata
    )


def _task_before_after_pair_count(tasks) -> int:
    pair_ids = {task.before_after_pair_id for task in tasks if task.before_after_pair_id}
    return len(pair_ids)


def generate_evidence_campaign_report(conn: Connection, persist_handoff: bool = True) -> EvidenceCampaignReport:
    tasks = list_tasks(conn)
    corpus = build_trace_corpus_report(conn)
    benchmark = build_benchmark_validation_report(list_benchmark_suite_runs(conn), tasks)
    telemetry = build_telemetry_corpus_report(conn)
    evidence_quality = build_evidence_quality_report(conn)

    required_real_traces = _required_trace_count(corpus)
    before_after_pairs = max(len(benchmark.before_after_pairs), _task_before_after_pair_count(tasks))
    benchmark_traces = benchmark.task_result_count

    handoff: Phase2HandoffPackage | None = None
    if persist_handoff:
        handoff = save_phase2_handoff_package(conn, generate_phase2_handoff_package(conn))

    real_trace_target = _target(
        "real_coding_agent_traces",
        "Real coding-agent traces",
        required_real_traces,
        25,
        "Phase 2.0 workload model uses this for execution graph shape, model/tool/I/O split, context lifetime, retry behavior, and outcomes.",
        "Capture Aider, SDK custom-agent, and local CLI-wrapped coding tasks with model/tool/file/terminal/context/outcome coverage.",
    )
    benchmark_target = _target(
        "benchmark_style_traces",
        "Benchmark-style traces",
        benchmark_traces,
        10,
        "Phase 2.1 uses this for repeatable workload slices and backend/system/hardware comparison planning.",
        "Record SWE-bench-style, Aider-style, OpenHands-style, or controlled bug-fix task results with linked traces.",
    )
    pair_target = _target(
        "before_after_pairs",
        "Before/after optimization pairs",
        before_after_pairs,
        5,
        "Phase 2.3 uses this to test whether repeated context and tool wait justify memory/cache/runtime architecture work.",
        "Create baseline and optimized traces for repeated-context and tool-wait tasks with success preservation metadata.",
    )
    telemetry_target = _target(
        "telemetry_backed_traces",
        "Telemetry-backed traces",
        telemetry.telemetry_task_count,
        3,
        "Phase 2.1 and Phase 2.3 use this for backend/system/hardware gap analysis, prefill/decode split, queueing, memory pressure, cache hit/miss evidence, and fabric/network symptoms where available.",
        "Import backend/system telemetry where available; Phase 2 owns the real backend/system/hardware experiments.",
    )

    required_outcome_target = _target(
        "outcome_metadata",
        "Useful traces with outcome metadata",
        sum(1 for task in corpus.task_summaries if task.has_outcome_metadata),
        25,
        "Phase 2 needs outcome preservation so architecture decisions do not optimize failed tasks.",
        "Attach task_success, tests_passed, tests_failed, patch_generated, files_changed_count, and retry_count where available.",
    )
    evidence_quality_target = _target(
        "evidence_quality_score",
        "Evidence quality score",
        evidence_quality.overall_score,
        75,
        "Phase 2 uses confidence labels to separate measured evidence from hypotheses and missing data.",
        "Regenerate evidence quality after adding real traces, benchmark records, before/after pairs, and telemetry.",
    )

    track_a = _track(
        "track_a_real_coding_agent_runs",
        "Track A: Real Coding-Agent Runs",
        "Capture real coding-agent workload shape, not toy prompt/response examples.",
        [real_trace_target, required_outcome_target],
        ["workload graph shape", "model/tool/I/O split", "context lifetime", "retry behavior", "outcome distribution"],
        [target.next_step for target in [real_trace_target, required_outcome_target] if target.status != "ready"],
        [
            "Run Aider and SDK custom-agent tasks against real repo edit/test workflows.",
            "Keep trace fields complete enough for Phase 2 workload modeling.",
        ],
    )
    track_b = _track(
        "track_b_benchmark_style_runs",
        "Track B: Benchmark-Style Runs",
        "Capture repeatable coding tasks with truth labels and clear run-mode boundaries.",
        [benchmark_target],
        ["repeatable workload slices", "success/failure outcomes", "backend comparison inputs"],
        [benchmark_target.next_step] if benchmark_target.status != "ready" else [],
        [
            "Add benchmark suite records with run_mode clearly marked as local, smoke, imported, dry_run, or official.",
            "Do not call local smoke records official benchmark results.",
        ],
    )
    track_c = _track(
        "track_c_before_after_pairs",
        "Track C: Before/After Optimization Pairs",
        "Measure whether Phase 1 optimization signals matter before Phase 2 turns them into architecture hypotheses.",
        [pair_target],
        ["repeated-context reduction", "tool-wait reduction", "success preservation", "memory/cache architecture signal"],
        [pair_target.next_step] if pair_target.status != "ready" else [],
        [
            "Pair baseline and optimized traces with before_after_pair_id.",
            "Record token, cost, latency, and task success changes.",
        ],
    )
    track_d = _track(
        "track_d_telemetry_imports",
        "Track D: Telemetry Imports, If Available",
        "Import backend/system/hardware telemetry when available, while keeping real experiments owned by Phase 2.",
        [telemetry_target],
        ["GPU/CPU utilization", "queue depth", "memory pressure", "TTFT/ITL", "prefill/decode timing", "cache hit/miss data", "fabric/network symptoms where available"],
        [telemetry_target.next_step] if telemetry_target.status != "ready" else [],
        [
            "Import telemetry for selected traces when a backend, runtime, gateway, or fabric layer exposes it.",
            "Treat missing telemetry as a Phase 2 test-plan item, not as evidence.",
        ],
    )

    minimum_exit_criteria = [
        real_trace_target,
        benchmark_target,
        pair_target,
        required_outcome_target,
        evidence_quality_target,
    ]
    strong_exit_criteria = [
        _target("strong_real_traces", "Strong corpus real traces", required_real_traces, 100, real_trace_target.phase2_use, real_trace_target.next_step),
        _target("strong_benchmark_traces", "Strong benchmark-style traces", benchmark_traces, 25, benchmark_target.phase2_use, benchmark_target.next_step),
        _target("strong_before_after_pairs", "Strong before/after pairs", before_after_pairs, 10, pair_target.phase2_use, pair_target.next_step),
        _target("real_backend_system_telemetry", "Real backend/system telemetry", telemetry.telemetry_task_count, 1, telemetry_target.phase2_use, telemetry_target.next_step),
    ]

    tracks = [track_a, track_b, track_c, track_d]
    score = round(
        real_trace_target.percent * 0.30
        + benchmark_target.percent * 0.20
        + pair_target.percent * 0.20
        + telemetry_target.percent * 0.10
        + required_outcome_target.percent * 0.10
        + min(100.0, evidence_quality.overall_score) * 0.10
    )
    campaign_status = "ready" if all(target.status == "ready" for target in minimum_exit_criteria) else "partial" if score > 0 else "missing"
    ready_for_workload_model = real_trace_target.status == "ready" and required_outcome_target.status == "ready"
    ready_for_backend_validation = benchmark_target.status == "ready" and pair_target.status == "ready"

    next_actions = []
    for track in tracks:
        next_actions.extend(track.missing_items)
    next_actions.extend(evidence_quality.next_steps[:4])
    next_actions = list(dict.fromkeys(next_actions))

    executive_summary = (
        f"Phase 1.6 Evidence Campaign status is {campaign_status} with score {score}/100. "
        f"Real trace coverage is {real_trace_target.current}/{real_trace_target.target}, "
        f"benchmark-style trace coverage is {benchmark_target.current}/{benchmark_target.target}, "
        f"before/after pair coverage is {pair_target.current}/{pair_target.target}, and "
        f"telemetry-backed trace coverage is {telemetry_target.current}/{telemetry_target.target}. "
        "This report measures readiness to feed the Phase 2 Agentic Inference System Blueprint; it does not claim real KV-cache hits, hardware speedup, or final architecture validation."
    )

    now = datetime.now(UTC).isoformat()
    return EvidenceCampaignReport(
        generated_at=now,
        executive_summary=executive_summary,
        campaign_status=campaign_status,  # type: ignore[arg-type]
        campaign_score=score,
        ready_for_phase2_workload_model=ready_for_workload_model,
        ready_for_phase2_backend_validation=ready_for_backend_validation,
        tracks=tracks,
        required_trace_fields=[
            "task_start",
            "task_end",
            "model_call_start/model_call_end",
            "tool_call_start/tool_call_end",
            "file_event",
            "terminal_event",
            "context_snapshot",
            "token counts",
            "cost estimate",
            "retry/backtrack metadata where possible",
            "task_success",
            "tests_passed/tests_failed",
            "patch_generated",
            "files_changed_count",
        ],
        minimum_exit_criteria=minimum_exit_criteria,
        strong_exit_criteria=strong_exit_criteria,
        regenerated_phase2_handoff_id=handoff.handoff_id if handoff else None,
        regenerated_phase2_entry_score=handoff.phase2_entry_criteria_score if handoff else None,
        no_claims=[
            "Do not claim official benchmark results from local, smoke, imported, or dry-run records.",
            "Do not claim real KV-cache hits without backend/system cache hit/miss telemetry.",
            "Do not claim hardware speedup without real backend/system/hardware measurement.",
            "Do not start Phase 2 architecture decisions before regenerating and reviewing the handoff package.",
            "Do not add unrelated product features under Phase 1.6.",
        ],
        next_actions=next_actions,
        source_reports={
            "trace_corpus": {"readiness_score": corpus.readiness_score, "readiness_status": corpus.readiness_status},
            "benchmark_validation": {"readiness_score": benchmark.readiness_score, "readiness_status": benchmark.readiness_status},
            "telemetry": {"readiness_score": telemetry.readiness_score, "readiness_status": telemetry.readiness_status},
            "evidence_quality": {"overall_score": evidence_quality.overall_score, "overall_status": evidence_quality.overall_status},
            "phase2_handoff": {
                "handoff_id": handoff.handoff_id if handoff else None,
                "entry_score": handoff.phase2_entry_criteria_score if handoff else None,
            },
        },
        created_at=now,
    )


def render_evidence_campaign_markdown(report: EvidenceCampaignReport) -> str:
    lines = [
        "# Phase 1.6 Evidence Campaign Report",
        "",
        f"- Campaign ID: `{report.campaign_id}`",
        f"- Version: `{report.campaign_version}`",
        f"- Mode: `{report.mode}`",
        f"- Generated: `{report.generated_at}`",
        f"- Status: **{report.campaign_status}**",
        f"- Score: **{report.campaign_score}/100**",
        f"- Regenerated Phase 2 system blueprint handoff: `{report.regenerated_phase2_handoff_id}`",
        f"- Regenerated Phase 2 entry score: **{report.regenerated_phase2_entry_score}/100**",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
        "## Campaign Tracks",
        "",
    ]
    for track in report.tracks:
        lines.extend([
            f"### {track.name}",
            "",
            f"- Status: **{track.status}**",
            f"- Summary: {track.summary}",
            "",
            "| Target | Current | Required | Status |",
            "|---|---:|---:|---|",
        ])
        lines.extend(f"| {target.label} | {target.current} | {target.target} | {target.status} |" for target in track.targets)
        lines.extend(["", "Phase 2 consumes:", ""])
        lines.extend(f"- {item}" for item in track.phase2_consumes)
        if track.missing_items:
            lines.extend(["", "Missing items:", ""])
            lines.extend(f"- {item}" for item in track.missing_items)
        lines.append("")
    lines.extend(["## Required Trace Fields", ""])
    lines.extend(f"- {item}" for item in report.required_trace_fields)
    lines.extend(["", "## Minimum Exit Criteria", ""])
    lines.extend(f"- {target.label}: {target.current}/{target.target} ({target.status})" for target in report.minimum_exit_criteria)
    lines.extend(["", "## No Claims", ""])
    lines.extend(f"- {item}" for item in report.no_claims)
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in report.next_actions[:20])
    return "\n".join(lines) + "\n"
