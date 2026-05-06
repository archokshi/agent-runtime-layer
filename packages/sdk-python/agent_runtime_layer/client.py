import json
from pathlib import Path
from urllib import request

from agent_runtime_layer.trace import TraceEvent


class AgentRuntimeClient:
    def __init__(self, base_url: str = "http://localhost:8000/api") -> None:
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        req = request.Request(f"{self.base_url}{path}", method="GET")
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def create_task(self, goal: str, project_id: str = "default", agent_type: str = "coding_agent") -> str:
        response = self._post("/tasks", {"project_id": project_id, "goal": goal, "agent_type": agent_type})
        return response["task_id"]

    def add_event(self, event: TraceEvent) -> dict:
        return self._post("/events", event.to_dict())

    def import_trace_file(self, path: str | Path) -> dict:
        return self._post("/traces/import", json.loads(Path(path).read_text()))

    def import_otel_file(self, path: str | Path) -> dict:
        return self._post("/traces/import/otel", json.loads(Path(path).read_text()))

    def export_task_otel(self, task_id: str) -> dict:
        return self._get(f"/tasks/{task_id}/otel")
