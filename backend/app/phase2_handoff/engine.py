from datetime import UTC, datetime
from sqlite3 import Connection

from app.benchmarking import build_benchmark_validation_report
from app.corpus.summary import build_trace_corpus_report
from app.evidence.quality import build_evidence_quality_report
from app.phase1_exit.engine import generate_phase1_exit_package
from app.schemas import Phase1TestPlanItem, Phase2HandoffPackage, Phase2HandoffSection
from app.storage.repositories import list_benchmark_suite_runs, list_tasks
from app.telemetry.summary import build_telemetry_corpus_report


def _status_from_score(score: int) -> str:
    if score >= 75:
        return "ready"
    if score > 0:
        return "partial"
    return "missing"


def _section(
    title: str,
    summary: str,
    status: str,
    evidence: dict,
    phase2_consumes: list[str],
    missing_items: list[str],
    next_steps: list[str],
) -> Phase2HandoffSection:
    return Phase2HandoffSection(
        title=title,
        summary=summary,
        status=status,  # type: ignore[arg-type]
        evidence=evidence,
        phase2_consumes=phase2_consumes,
        missing_items=missing_items,
        next_steps=next_steps,
    )


def generate_phase2_handoff_package(conn: Connection) -> Phase2HandoffPackage:
    corpus = build_trace_corpus_report(conn)
    benchmark = build_benchmark_validation_report(list_benchmark_suite_runs(conn), list_tasks(conn))
    telemetry = build_telemetry_corpus_report(conn)
    evidence_quality = build_evidence_quality_report(conn)
    phase1_exit = generate_phase1_exit_package(conn)

    entry_score = round(
        (
            corpus.readiness_score
            + benchmark.readiness_score
            + telemetry.readiness_score
            + evidence_quality.overall_score
            + phase1_exit.architecture_readiness_score
        )
        / 5
    )
    entry_status = _status_from_score(entry_score)

    missing_evidence = sorted(
        set(
            corpus.next_steps
            + benchmark.next_steps
            + telemetry.next_steps
            + evidence_quality.missing_evidence
        )
    )

    workload_model_input = _section(
        "Phase 2.0 Agentic Inference Workload Model",
        "Trace corpus evidence for execution graphs, model/tool/I/O split, context lifetime, retry structure, and outcome distribution.",
        corpus.readiness_status,
        {
            "trace_target": corpus.target_trace_count,
            "trace_metrics": [metric.model_dump() for metric in corpus.metrics],
            "phase2_evidence_needs": [need.model_dump() for need in corpus.phase2_evidence_needs],
        },
        [
            "execution graph shape",
            "model/tool/CPU/I/O split",
            "retry/backtrack structure",
            "context lifetime",
            "outcome distribution",
        ],
        [item for item in corpus.next_steps if corpus.readiness_status != "ready"],
        corpus.next_steps,
    )

    backend_gap_analysis_input = _section(
        "Phase 2.1 Existing Backend/System/Hardware Gap Analysis",
        "Benchmark and telemetry evidence for comparing current backends, runtime/system behavior, cache-aware serving, queueing, utilization, memory pressure, and fabric/network symptoms where available.",
        "ready" if benchmark.readiness_status == "ready" and telemetry.readiness_status == "ready" else "partial" if benchmark.task_result_count or telemetry.sample_count else "missing",
        {
            "benchmark_readiness": benchmark.model_dump(),
            "telemetry_readiness": telemetry.model_dump(),
        },
        [
            "official vs local benchmark truth labels",
            "repeatable workload slices",
            "GPU/CPU utilization",
            "queue depth",
            "prefill/decode timing",
            "cache hit/miss behavior",
        ],
        benchmark.next_steps + telemetry.next_steps,
        [
            "Run 10-25 linked benchmark tasks with trace completion and outcome metadata.",
            "Import telemetry from the current backend/system path and at least one prefix-cache-capable backend.",
        ],
    )

    runtime_hardware_interface_input = _section(
        "Phase 2.2 Runtime-System-Hardware Interface",
        "Signals needed to define runtime/system hints such as graph ID, stable prefix ID, context fingerprint, retry boundary, priority, prefill/decode class, cache retention hint, memory tier hint, and fabric/network symptoms where available.",
        "partial" if corpus.task_summaries else "missing",
        {
            "context_coverage": next((item.model_dump() for item in corpus.coverage if item.category == "Context snapshots"), {}),
            "telemetry_fields": [field.model_dump() for field in telemetry.field_coverage],
        },
        [
            "execution graph ID",
            "stable prefix/context fingerprints",
            "retry boundary",
            "priority/SLO hints",
            "prefill/decode class",
            "cache retention hints",
        ],
        [
            "Need stronger context hash coverage across real traces.",
            "Need backend cache-hit metrics before defining cache-retention confidence.",
        ],
        [
            "Use SDK/adapters to log stable/dynamic context blocks.",
            "Attach backend/system telemetry fields to model-call spans where possible.",
        ],
    )

    memory_context_architecture_input = _section(
        "Phase 2.3 Memory/KV/Context Architecture",
        "Evidence for persistent prefix/KV memory, warm context tier, memory pressure, and cache hit/miss behavior.",
        "partial" if evidence_quality.overall_score > 0 else "missing",
        {
            "context_metrics": phase1_exit.workload_evaluation_package.get("context_kv_reuse_profile", {}),
            "telemetry_memory_cache": [
                field.model_dump()
                for field in telemetry.field_coverage
                if field.field in {"gpu_memory_used_percent", "kv_cache_hit_rate"}
            ],
        },
        [
            "persistent prefix/KV cache",
            "warm context tier",
            "memory hierarchy",
            "cache retention/eviction",
            "KV/cache hit validation",
        ],
        [
            "KV/cache hit rate is missing unless imported telemetry provides it.",
            "Memory pressure needs more real backend samples.",
        ],
        [
            "Compare repeated-context traces against cache-aware backends.",
            "Record memory usage and cache hit/miss metrics during those runs.",
        ],
    )

    compiler_execution_graph_input = _section(
        "Phase 2.4 Agentic Compiler / Execution Graph Model",
        "Trace and scheduler evidence for graph IR, dependency planning, retry checkpointing, tool-wait overlap, system bottleneck mapping, and backend placement.",
        "partial" if corpus.task_summaries else "missing",
        {
            "execution_graph_coverage": next((item.model_dump() for item in corpus.coverage if item.category == "Complete execution traces"), {}),
            "scheduler_signal": phase1_exit.workload_evaluation_package.get("tool_io_orchestration_profile", {}),
        },
        [
            "execution graph IR",
            "dependency graph",
            "tool-wait overlap",
            "retry checkpoint planning",
            "backend placement hints",
        ],
        [
            "Need more traces with parent_span_id quality and retry/backtrack events.",
            "Need real scheduler experiments before production scheduling claims.",
        ],
        [
            "Capture parent-child span relationships from real coding agents.",
            "Create benchmark before/after scheduler experiments.",
        ],
    )

    evidence_quality_gate = _section(
        "Evidence Quality Gate",
        "Rules that determine whether Phase 2 may use a metric as architecture evidence, hypothesis, or instrumentation gap.",
        evidence_quality.overall_status,
        evidence_quality.model_dump(),
        [
            "measured metrics as primary evidence",
            "estimated metrics as hypotheses",
            "inferred metrics as instrumentation priorities",
            "missing metrics as do-not-use boundaries",
        ],
        evidence_quality.missing_evidence,
        evidence_quality.next_steps,
    )

    phase2_test_plan = [
        Phase1TestPlanItem(
            platform="Phase 2.0 workload model",
            test="Build the agentic inference workload model from the Phase 1.5 handoff sections.",
            metrics=["trace coverage", "event coverage", "context coverage", "outcome coverage"],
            success_criteria="Every workload-model claim maps to measured or estimated Phase 1 evidence.",
        ),
        Phase1TestPlanItem(
            platform="Phase 2.1 backend/system/hardware gap analysis",
            test="Compare current backend/system path against at least one cache-aware backend using linked benchmark traces.",
            metrics=["TTFT", "ITL", "queue depth", "GPU utilization", "cache hit rate", "task success"],
            success_criteria="Backend gap conclusions separate measured results from hypotheses.",
        ),
        Phase1TestPlanItem(
            platform="Phase 2.2 runtime-system-hardware interface",
            test="Draft runtime hints from available trace fields and mark missing signal confidence.",
            metrics=["stable prefix IDs", "context hashes", "retry boundaries", "prefill/decode class"],
            success_criteria="Every proposed hint is consumed by a Phase 2 architecture or backend test.",
        ),
        Phase1TestPlanItem(
            platform="Phase 2.3 memory/KV/context architecture",
            test="Validate repeated-context opportunity against real cache-hit telemetry where possible.",
            metrics=["repeated tokens", "KV/cache hit rate", "memory usage", "prefill time"],
            success_criteria="Memory/KV claims do not rely on repeated-context estimates alone.",
        ),
    ]

    phase2_do_not_claim = [
        "Do not claim official benchmark performance unless run_mode=official and external harness evidence exists.",
        "Do not claim real KV-cache hits unless backend/system telemetry includes cache hit/miss metrics.",
        "Do not claim hardware speedup, utilization improvement, or silicon ROI without measured backend/system/hardware experiments.",
        "Do not turn repeated-context estimates into architecture requirements without Phase 2 validation.",
        "Do not build RTL, FPGA, ASIC, or hardware simulation from this handoff alone.",
    ]

    executive_summary = (
        "Phase 1.5 packages Agent Runtime Layer evidence for the Phase 2 Agentic Inference System Blueprint. "
        f"Entry status is {entry_status} with score {entry_score}/100. "
        "Phase 2 may use measured trace evidence now, but benchmark officiality, backend/system telemetry coverage, "
        "real cache-hit evidence, fabric/network evidence, and hardware speedup evidence remain gated by missing measurements."
    )

    return Phase2HandoffPackage(
        generated_at=datetime.now(UTC).isoformat(),
        executive_summary=executive_summary,
        phase2_entry_criteria_status=entry_status,  # type: ignore[arg-type]
        phase2_entry_criteria_score=entry_score,
        workload_model_input=workload_model_input,
        backend_gap_analysis_input=backend_gap_analysis_input,
        runtime_hardware_interface_input=runtime_hardware_interface_input,
        memory_context_architecture_input=memory_context_architecture_input,
        compiler_execution_graph_input=compiler_execution_graph_input,
        evidence_quality_gate=evidence_quality_gate,
        missing_evidence_checklist=missing_evidence,
        phase2_test_plan=phase2_test_plan,
        phase2_do_not_claim=phase2_do_not_claim,
        source_reports={
            "trace_corpus": {"readiness_score": corpus.readiness_score, "readiness_status": corpus.readiness_status},
            "benchmark_validation": {"readiness_score": benchmark.readiness_score, "readiness_status": benchmark.readiness_status},
            "telemetry": {"readiness_score": telemetry.readiness_score, "readiness_status": telemetry.readiness_status},
            "evidence_quality": {"overall_score": evidence_quality.overall_score, "overall_status": evidence_quality.overall_status},
            "phase1_exit": {"architecture_readiness_score": phase1_exit.architecture_readiness_score},
        },
        created_at=datetime.now(UTC).isoformat(),
    )


def render_phase2_handoff_markdown(report: Phase2HandoffPackage) -> str:
    sections = [
        report.workload_model_input,
        report.backend_gap_analysis_input,
        report.runtime_hardware_interface_input,
        report.memory_context_architecture_input,
        report.compiler_execution_graph_input,
        report.evidence_quality_gate,
    ]
    lines = [
        "# Phase 1.5 Phase 2 System Blueprint Handoff Package",
        "",
        f"- Handoff ID: `{report.handoff_id}`",
        f"- Version: `{report.package_version}`",
        f"- Mode: `{report.mode}`",
        f"- Generated: `{report.generated_at}`",
        f"- Phase 2 entry status: **{report.phase2_entry_criteria_status}**",
        f"- Phase 2 entry score: **{report.phase2_entry_criteria_score}/100**",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
    ]
    for section in sections:
        lines.extend([
            f"## {section.title}",
            "",
            f"- Status: **{section.status}**",
            f"- Summary: {section.summary}",
            "",
            "Phase 2 consumes:",
            "",
        ])
        lines.extend(f"- {item}" for item in section.phase2_consumes)
        if section.missing_items:
            lines.extend(["", "Missing items:", ""])
            lines.extend(f"- {item}" for item in section.missing_items[:20])
        if section.next_steps:
            lines.extend(["", "Next steps:", ""])
            lines.extend(f"- {item}" for item in section.next_steps[:10])
        lines.append("")
    lines.extend(["## Phase 2 Test Plan", ""])
    lines.extend(f"- **{item.platform}**: {item.test} Success: {item.success_criteria}" for item in report.phase2_test_plan)
    lines.extend(["", "## Do Not Claim", ""])
    lines.extend(f"- {item}" for item in report.phase2_do_not_claim)
    return "\n".join(lines) + "\n"
