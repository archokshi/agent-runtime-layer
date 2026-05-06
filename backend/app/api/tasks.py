from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.schemas import Task, TaskCreate, TaskCreateResponse
from app.storage.repositories import create_task, get_task, list_tasks

router = APIRouter()


@router.post("/tasks", response_model=TaskCreateResponse)
def create_task_endpoint(task: TaskCreate) -> TaskCreateResponse:
    with get_conn() as conn:
        task_id = create_task(conn, task)
    return TaskCreateResponse(task_id=task_id)


@router.get("/tasks", response_model=list[Task])
def list_tasks_endpoint() -> list[Task]:
    with get_conn() as conn:
        return list_tasks(conn)


@router.get("/tasks/{task_id}", response_model=Task)
def get_task_endpoint(task_id: str) -> Task:
    with get_conn() as conn:
        task = get_task(conn, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
