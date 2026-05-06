from typing import Any

from fastapi import APIRouter, HTTPException

from app.analyzer.engine import analyze_events, generate_blueprint
from app.db import get_conn
from app.otel import otel_to_trace, trace_to_otel
from app.schemas import TraceImport, TraceImportResponse
from app.storage.repositories import add_event, create_task, get_task, list_events, save_analysis, save_blueprint

router = APIRouter()


@router.post("/traces/import", response_model=TraceImportResponse)
def import_trace(trace: TraceImport) -> TraceImportResponse:
    task = trace.task.model_copy(update={"project_id": trace.project_id})
    with get_conn() as conn:
        task_id = create_task(conn, task)
        events = sorted(
            [event.model_copy(update={"task_id": task_id}) for event in trace.events],
            key=lambda event: event.timestamp,
        )
        for event in events:
            add_event(conn, event)
        report = analyze_events(task_id, events)
        preview = generate_blueprint(task_id, report)
        save_analysis(conn, report)
        save_blueprint(conn, preview)
    return TraceImportResponse(task_id=task_id, event_count=len(trace.events))


@router.get("/tasks/{task_id}/otel")
def export_task_otel(task_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        events = list_events(conn, task_id)
    return trace_to_otel(task, events)


@router.post("/traces/import/otel", response_model=TraceImportResponse)
def import_otel_trace(payload: dict[str, Any]) -> TraceImportResponse:
    try:
        trace = otel_to_trace(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return import_trace(trace)
