from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.schemas import Task, TaskCreate, TaskCreateResponse
from app.storage.repositories import create_task, get_task, list_tasks

router = APIRouter()

STALE_THRESHOLD_MINUTES = 30


def _auto_complete_stale(conn) -> None:
    """Mark running tasks older than 30 min as completed — handles orphaned sessions
    where the Stop hook never fired (e.g. process killed, terminal closed)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)).isoformat()
    conn.execute(
        """UPDATE tasks SET status = 'completed', ended_at = ?
           WHERE status = 'running' AND created_at < ?""",
        [datetime.now(timezone.utc).isoformat(), cutoff],
    )


@router.post("/tasks", response_model=TaskCreateResponse)
def create_task_endpoint(task: TaskCreate) -> TaskCreateResponse:
    with get_conn() as conn:
        task_id = create_task(conn, task)
    return TaskCreateResponse(task_id=task_id)


@router.get("/tasks", response_model=list[Task])
def list_tasks_endpoint() -> list[Task]:
    with get_conn() as conn:
        _auto_complete_stale(conn)
        return list_tasks(conn)


@router.get("/tasks/{task_id}", response_model=Task)
def get_task_endpoint(task_id: str) -> Task:
    with get_conn() as conn:
        task = get_task(conn, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
