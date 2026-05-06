from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.schemas import Event
from app.storage.repositories import add_event, get_task, list_events

router = APIRouter()


@router.post("/events", response_model=Event)
def add_event_endpoint(event: Event) -> Event:
    with get_conn() as conn:
        if get_task(conn, event.task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        add_event(conn, event)
    return event


@router.get("/tasks/{task_id}/events", response_model=list[Event])
def list_events_endpoint(task_id: str) -> list[Event]:
    with get_conn() as conn:
        if get_task(conn, task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return list_events(conn, task_id)
