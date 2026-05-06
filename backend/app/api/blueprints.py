from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.db import get_conn
from app.hardware.analysis import analyze_hardware
from app.schemas import SiliconBlueprintGenerateRequest, SiliconBlueprintReport, TraceReplayReport, TraceReplayRequest
from app.silicon_blueprint.engine import generate_silicon_blueprint
from app.storage.repositories import (
    get_silicon_blueprint_report,
    get_task,
    get_trace_replay_report,
    list_events,
    list_hardware_telemetry_samples,
    list_silicon_blueprint_reports,
    list_tasks,
    list_trace_replay_reports,
    save_silicon_blueprint_report,
    save_trace_replay_report,
)
from app.trace_replay.engine import replay_blueprint

router = APIRouter()


def _format_metrics(metrics: dict) -> str:
    if not metrics:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in metrics.items())


def render_blueprint_markdown(report: SiliconBlueprintReport) -> str:
    lines = [
        f"# {report.name}",
        "",
        f"- Blueprint ID: `{report.blueprint_id}`",
        f"- Version: `{report.blueprint_version}`",
        f"- Mode: `{report.mode}`",
        f"- Created: `{report.created_at}`",
        "",
        "## Workload Profile",
        "",
        f"- Tasks analyzed: {report.workload_profile.task_count}",
        f"- Model calls: {report.workload_profile.model_call_count}",
        f"- Tool calls: {report.workload_profile.tool_call_count}",
        f"- Input tokens: {report.workload_profile.total_input_tokens}",
        f"- Output tokens: {report.workload_profile.total_output_tokens}",
        f"- Estimated cost: ${report.workload_profile.total_cost_dollars:.6f}",
        f"- Average repeated context: {report.workload_profile.avg_repeated_context_percent:.2f}%",
        f"- Average cache reuse opportunity: {report.workload_profile.avg_cache_reuse_opportunity_percent:.2f}%",
        "",
        "## Validation Summary",
        "",
        f"- Local trace count: {report.validation_summary.local_trace_count}",
        f"- Target trace count: {report.validation_summary.target_trace_count}",
        f"- Target progress: {report.validation_summary.target_progress_percent:.2f}%",
        f"- Tasks with hardware telemetry: {report.validation_summary.tasks_with_hardware_telemetry}",
        f"- Status: `{report.validation_summary.real_world_validation_status}`",
        "",
        "## Bottleneck Map",
        "",
    ]
    lines.extend(f"- {category}: {count}" for category, count in report.bottleneck_map.items())
    lines.extend(["", "## Memory Hierarchy Recommendations", ""])
    lines.extend(
        f"- **{rec.title}** ({rec.priority}, confidence {round(rec.confidence * 100)}%): {rec.rationale} Metrics: {_format_metrics(rec.metrics)}"
        for rec in report.memory_hierarchy_recommendations
    )
    lines.extend(["", "## Hardware Primitive Ranking", ""])
    lines.extend(
        f"{index}. **{primitive.primitive}** score {primitive.score:.2f}: {primitive.rationale} Evidence: {_format_metrics(primitive.evidence)}"
        for index, primitive in enumerate(report.hardware_primitive_rankings, start=1)
    )
    lines.extend(["", "## Backend And Runtime Recommendations", ""])
    lines.extend(
        f"- **{rec.title}** ({rec.priority}, confidence {round(rec.confidence * 100)}%): {rec.rationale} Metrics: {_format_metrics(rec.metrics)}"
        for rec in report.backend_runtime_recommendations
    )
    lines.extend(["", "## Benchmark Proposals", ""])
    lines.extend(
        f"- **{rec.title}** ({rec.priority}, confidence {round(rec.confidence * 100)}%): {rec.rationale}"
        for rec in report.benchmark_proposals
    )
    lines.extend(["", "## Remaining Validation Items", ""])
    lines.extend(f"- {item}" for item in report.validation_summary.remaining_validation_items)
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    return "\n".join(lines) + "\n"


def render_replay_markdown(report: TraceReplayReport) -> str:
    lines = [
        f"# Trace Replay Report {report.replay_id}",
        "",
        f"- Blueprint ID: `{report.blueprint_id}`",
        f"- Simulator version: `{report.simulator_version}`",
        f"- Mode: `{report.mode}`",
        f"- Best scenario: `{report.best_scenario_id}`",
        f"- Created: `{report.created_at}`",
        "",
        "## Comparison Summary",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in report.comparison_summary.items())
    lines.extend(["", "## Scenario Results", ""])
    for scenario in report.scenario_results:
        lines.extend([
            f"### {scenario.name}",
            "",
            f"- Scenario ID: `{scenario.scenario_id}`",
            f"- Duration reduction: {scenario.delta.duration_reduction_percent:.2f}%",
            f"- Input token reduction: {scenario.delta.input_token_reduction_percent:.2f}%",
            f"- Estimated cost reduction: {scenario.delta.estimated_cost_reduction_percent:.2f}%",
            f"- Estimated prefill reduction: {scenario.delta.estimated_prefill_reduction_percent:.2f}%",
            f"- Queue pressure reduction: {scenario.delta.queue_pressure_reduction_percent:.2f}%",
            f"- Confidence: {round(scenario.confidence * 100)}%",
            f"- Confidence reason: {scenario.projection_confidence_reason}",
            f"- Requires real backend validation: {scenario.requires_real_backend_validation}",
            "",
            "Validation evidence needed:",
        ])
        lines.extend(f"- {item}" for item in scenario.validation_evidence_needed)
        lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    return "\n".join(lines) + "\n"


@router.post("/blueprints/generate", response_model=SiliconBlueprintReport)
def generate_blueprint_report(payload: SiliconBlueprintGenerateRequest) -> SiliconBlueprintReport:
    with get_conn() as conn:
        if payload.task_ids:
            tasks = []
            for task_id in payload.task_ids:
                task = get_task(conn, task_id)
                if task is None:
                    raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
                tasks.append(task)
        else:
            tasks = list_tasks(conn)
        if not tasks:
            raise HTTPException(status_code=400, detail="No tasks available for blueprint generation")
        events_by_task = {task.task_id: list_events(conn, task.task_id) for task in tasks}
        hardware_reports = {}
        for task in tasks:
            samples = list_hardware_telemetry_samples(conn, task.task_id)
            hardware_reports[task.task_id] = analyze_hardware(task.task_id, events_by_task[task.task_id], samples) if samples else None
        report = generate_silicon_blueprint(payload.name, tasks, events_by_task, hardware_reports)
        save_silicon_blueprint_report(conn, report)
        return report


@router.get("/blueprints", response_model=list[SiliconBlueprintReport])
def list_blueprints() -> list[SiliconBlueprintReport]:
    with get_conn() as conn:
        return list_silicon_blueprint_reports(conn)


@router.get("/blueprints/{blueprint_id}", response_model=SiliconBlueprintReport)
def get_blueprint_report(blueprint_id: str) -> SiliconBlueprintReport:
    with get_conn() as conn:
        report = get_silicon_blueprint_report(conn, blueprint_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Blueprint report not found")
    return report


@router.get("/blueprints/{blueprint_id}/export.md", response_class=PlainTextResponse)
def export_blueprint_markdown(blueprint_id: str) -> str:
    with get_conn() as conn:
        report = get_silicon_blueprint_report(conn, blueprint_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Blueprint report not found")
    return render_blueprint_markdown(report)


@router.post("/blueprints/{blueprint_id}/simulate", response_model=TraceReplayReport)
def simulate_blueprint(blueprint_id: str, payload: TraceReplayRequest | None = None) -> TraceReplayReport:
    with get_conn() as conn:
        blueprint = get_silicon_blueprint_report(conn, blueprint_id)
        if blueprint is None:
            raise HTTPException(status_code=404, detail="Blueprint report not found")
        tasks = []
        for task_id in blueprint.task_ids:
            task = get_task(conn, task_id)
            if task is not None:
                tasks.append(task)
        if not tasks:
            raise HTTPException(status_code=400, detail="Blueprint has no available local tasks to replay")
        events_by_task = {task.task_id: list_events(conn, task.task_id) for task in tasks}
        hardware_reports = {}
        for task in tasks:
            samples = list_hardware_telemetry_samples(conn, task.task_id)
            hardware_reports[task.task_id] = analyze_hardware(task.task_id, events_by_task[task.task_id], samples) if samples else None
        report = replay_blueprint(blueprint, tasks, events_by_task, hardware_reports, payload.scenario_ids if payload else None)
        save_trace_replay_report(conn, report)
        return report


@router.get("/blueprints/{blueprint_id}/replays", response_model=list[TraceReplayReport])
def list_blueprint_replays(blueprint_id: str) -> list[TraceReplayReport]:
    with get_conn() as conn:
        blueprint = get_silicon_blueprint_report(conn, blueprint_id)
        if blueprint is None:
            raise HTTPException(status_code=404, detail="Blueprint report not found")
        return list_trace_replay_reports(conn, blueprint_id)


@router.get("/replays/{replay_id}", response_model=TraceReplayReport)
def get_replay_report(replay_id: str) -> TraceReplayReport:
    with get_conn() as conn:
        report = get_trace_replay_report(conn, replay_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace replay report not found")
    return report


@router.get("/replays/{replay_id}/export.md", response_class=PlainTextResponse)
def export_replay_markdown(replay_id: str) -> str:
    with get_conn() as conn:
        report = get_trace_replay_report(conn, replay_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace replay report not found")
    return render_replay_markdown(report)
