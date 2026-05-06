from fastapi import APIRouter, HTTPException

from app.analyzer.engine import (
    analyze_events,
    generate_blueprint,
    generate_optimization_recommendations,
    generate_validation_report,
)
from app.backend_runtime.hints import generate_backend_hints
from app.db import get_conn
from app.hardware.analysis import analyze_hardware
from app.optimizer.context import optimize_context
from app.scheduler.engine import schedule_task
from app.schemas import AnalysisReport, BackendAwareReport, BlueprintPreview, ContextOptimizationReport, HardwareAnalysisReport, HardwareTelemetryImport, HardwareTelemetryImportResponse, OptimizationReport, SchedulerReport, ValidationReport
from app.storage.repositories import (
    add_hardware_telemetry_samples,
    get_backend_aware_report,
    get_context_optimization_report,
    get_scheduler_report,
    get_task,
    list_hardware_telemetry_samples,
    list_events,
    list_tasks_by_pair,
    save_analysis,
    save_backend_aware_report,
    save_blueprint,
    save_context_optimization_report,
    save_hardware_analysis_report,
    save_scheduler_report,
)

router = APIRouter()


@router.get("/tasks/{task_id}/analysis", response_model=AnalysisReport)
def get_analysis(task_id: str) -> AnalysisReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = analyze_events(task_id, list_events(conn, task_id))
        save_analysis(conn, report)
        return report


@router.get("/tasks/{task_id}/blueprint", response_model=BlueprintPreview)
def get_blueprint(task_id: str) -> BlueprintPreview:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = analyze_events(task_id, list_events(conn, task_id))
        preview = generate_blueprint(task_id, report)
        save_analysis(conn, report)
        save_blueprint(conn, preview)
        return preview


@router.get("/tasks/{task_id}/optimizations", response_model=OptimizationReport)
def get_optimizations(task_id: str) -> OptimizationReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = analyze_events(task_id, list_events(conn, task_id))
        save_analysis(conn, report)
        return generate_optimization_recommendations(task_id, report)


@router.get("/tasks/{task_id}/validation", response_model=ValidationReport)
def get_validation(task_id: str) -> ValidationReport:
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = analyze_events(task_id, list_events(conn, task_id))
        save_analysis(conn, report)
        paired_tasks = list_tasks_by_pair(conn, task.before_after_pair_id) if task.before_after_pair_id else []
        paired_reports = {
            paired.task_id: analyze_events(paired.task_id, list_events(conn, paired.task_id))
            for paired in paired_tasks
        }
        return generate_validation_report(task, report, paired_tasks, paired_reports)


@router.post("/tasks/{task_id}/optimize-context", response_model=ContextOptimizationReport)
def optimize_context_endpoint(task_id: str) -> ContextOptimizationReport:
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        events = list_events(conn, task_id)
        report = optimize_context(task, events)
        save_context_optimization_report(conn, report)
        return report


@router.get("/tasks/{task_id}/optimized-context", response_model=ContextOptimizationReport)
def get_optimized_context(task_id: str) -> ContextOptimizationReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = get_context_optimization_report(conn, task_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Context optimization report not found")
        return report


@router.post("/tasks/{task_id}/schedule", response_model=SchedulerReport)
def schedule_task_endpoint(task_id: str) -> SchedulerReport:
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = schedule_task(task, list_events(conn, task_id))
        save_scheduler_report(conn, report)
        return report


@router.get("/tasks/{task_id}/schedule", response_model=SchedulerReport)
def get_schedule_report(task_id: str) -> SchedulerReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = get_scheduler_report(conn, task_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Scheduler report not found")
        return report


@router.post("/tasks/{task_id}/backend-hints", response_model=BackendAwareReport)
def backend_hints_endpoint(task_id: str) -> BackendAwareReport:
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = generate_backend_hints(task, list_events(conn, task_id))
        save_backend_aware_report(conn, report)
        return report


@router.get("/tasks/{task_id}/backend-hints", response_model=BackendAwareReport)
def get_backend_hints(task_id: str) -> BackendAwareReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        report = get_backend_aware_report(conn, task_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backend hint report not found")
        return report


@router.post("/tasks/{task_id}/telemetry/import", response_model=HardwareTelemetryImportResponse)
def import_hardware_telemetry(task_id: str, payload: HardwareTelemetryImport) -> HardwareTelemetryImportResponse:
    if payload.task_id != task_id:
        raise HTTPException(status_code=400, detail="Telemetry task_id must match path task_id")
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        samples = [sample.model_copy(update={"task_id": task_id}) for sample in payload.samples]
        count = add_hardware_telemetry_samples(conn, samples)
        report = analyze_hardware(task_id, list_events(conn, task_id), list_hardware_telemetry_samples(conn, task_id))
        save_hardware_analysis_report(conn, report)
    return HardwareTelemetryImportResponse(task_id=task_id, sample_count=count)


@router.get("/tasks/{task_id}/hardware-analysis", response_model=HardwareAnalysisReport)
def get_hardware_analysis(task_id: str) -> HardwareAnalysisReport:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        samples = list_hardware_telemetry_samples(conn, task_id)
        if not samples:
            raise HTTPException(status_code=404, detail="Hardware telemetry not found")
        report = analyze_hardware(task_id, list_events(conn, task_id), samples)
        save_hardware_analysis_report(conn, report)
        return report
