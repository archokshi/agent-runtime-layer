import json
import re

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.schemas import Event
from app.storage.repositories import add_event, get_task, list_events

router = APIRouter()


def _sanitize(obj):
    """Recursively strip surrogate characters from strings so JSON serialization never fails."""
    if isinstance(obj, str):
        return obj.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _sanitize_event(event: Event) -> Event:
    event.attributes = _sanitize(event.attributes)
    event.payload    = _sanitize(event.payload)
    return event


@router.post("/events", response_model=Event)
def add_event_endpoint(event: Event) -> Event:
    with get_conn() as conn:
        if get_task(conn, event.task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        add_event(conn, _sanitize_event(event))
    return event


@router.get("/tasks/{task_id}/events", response_model=list[Event])
def list_events_endpoint(task_id: str) -> list[Event]:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return [_sanitize_event(e) for e in list_events(conn, task_id)]
