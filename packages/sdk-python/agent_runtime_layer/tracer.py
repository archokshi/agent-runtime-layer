import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import Any
from uuid import uuid4

from agent_runtime_layer.capture import DEFAULT_TRACE_DIR
from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.redaction import redact_value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def stable_hash(value: str, prefix: str = "sha256") -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def prompt_hash(prompt: str) -> str:
    return stable_hash(prompt)


def context_hash(context: str) -> str:
    return stable_hash(context)


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    input_cost_per_million: float = 0.0,
    output_cost_per_million: float = 0.0,
) -> float:
    return round(
        (input_tokens / 1_000_000 * input_cost_per_million)
        + (output_tokens / 1_000_000 * output_cost_per_million),
        6,
    )


@dataclass
class TraceWriteResult:
    task_id: str
    trace_path: Path


class ModelCallSpan:
    def __init__(
        self,
        tracer: "AgentRuntimeTracer",
        model: str,
        role: str,
        estimated_input_tokens: int = 0,
        expected_output_tokens: int = 0,
        prompt_hash_value: str | None = None,
        name: str = "model_call",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.tracer = tracer
        self.model = model
        self.role = role
        self.estimated_input_tokens = estimated_input_tokens
        self.expected_output_tokens = expected_output_tokens
        self.prompt_hash_value = prompt_hash_value or "sha256:unknown"
        self.name = name
        self.attributes = attributes or {}
        self.span_id = f"span_model_{uuid4().hex[:8]}"
        self.started_at = 0.0
        self.finished = False

    def __enter__(self) -> "ModelCallSpan":
        self.started_at = time.perf_counter()
        self.tracer.add_event(
            event_type="model_call_start",
            span_id=self.span_id,
            parent_span_id=self.tracer.task_span_id,
            name=self.name,
            attributes={
                "model": self.model,
                "role": self.role,
                "estimated_input_tokens": self.estimated_input_tokens,
                "expected_output_tokens": self.expected_output_tokens,
                "prompt_hash": self.prompt_hash_value,
                **self.attributes,
            },
        )
        return self

    def finish(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_dollars: float | None = None,
        status: str = "success",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        latency_ms = int((time.perf_counter() - self.started_at) * 1000)
        self.tracer.add_event(
            event_type="model_call_end",
            span_id=self.span_id,
            parent_span_id=self.tracer.task_span_id,
            name=f"{self.name}_end",
            attributes={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_dollars": float(cost_dollars or 0.0),
                "status": status,
                **(attributes or {}),
            },
        )
        self.finished = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self.finished:
            self.finish(status="error" if exc else "success")


class ToolCallSpan:
    def __init__(
        self,
        tracer: "AgentRuntimeTracer",
        tool_name: str,
        command: str | None = None,
        risk_level: str = "unknown",
        name: str = "tool_call",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.tracer = tracer
        self.tool_name = tool_name
        self.command = command
        self.risk_level = risk_level
        self.name = name
        self.attributes = attributes or {}
        self.span_id = f"span_tool_{uuid4().hex[:8]}"
        self.started_at = 0.0
        self.finished = False

    def __enter__(self) -> "ToolCallSpan":
        self.started_at = time.perf_counter()
        self.tracer.add_event(
            event_type="tool_call_start",
            span_id=self.span_id,
            parent_span_id=self.tracer.task_span_id,
            name=self.name,
            attributes={
                "tool_name": self.tool_name,
                "command": self.command,
                "risk_level": self.risk_level,
                **self.attributes,
            },
        )
        return self

    def finish(
        self,
        status: str = "success",
        exit_code: int | None = 0,
        attributes: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        latency_ms = int((time.perf_counter() - self.started_at) * 1000)
        if payload:
            self.tracer.add_event(
                event_type="terminal_event",
                span_id=f"span_terminal_{uuid4().hex[:8]}",
                parent_span_id=self.span_id,
                name=f"{self.name}_output",
                attributes={
                    "command": self.command,
                    "duration_ms": latency_ms,
                    "exit_code": exit_code,
                    **(attributes or {}),
                },
                payload=payload,
            )
        self.tracer.add_event(
            event_type="tool_call_end",
            span_id=self.span_id,
            parent_span_id=self.tracer.task_span_id,
            name=f"{self.name}_end",
            attributes={
                "latency_ms": latency_ms,
                "status": status,
                "exit_code": exit_code,
                **(attributes or {}),
            },
        )
        self.finished = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self.finished:
            self.finish(status="failed" if exc else "success", exit_code=1 if exc else 0)


class AgentRuntimeTracer:
    def __init__(
        self,
        task_name: str,
        project_id: str = "default",
        trace_dir: Path | str = DEFAULT_TRACE_DIR,
        task_id: str | None = None,
        agent_type: str = "custom_agent",
        budget_dollars: float | None = None,
        latency_slo_seconds: int | None = None,
        auto_optimize: bool = False,
        max_retries: int | None = None,
        max_cost_per_run: float | None = None,
    ) -> None:
        self.task_name = task_name
        self.project_id = project_id
        self.trace_dir = Path(trace_dir)
        self.task_id = task_id or f"task_sdk_{uuid4().hex[:12]}"
        self.agent_type = agent_type
        self.budget_dollars = budget_dollars
        self.latency_slo_seconds = latency_slo_seconds
        # Phase 1.7: auto_optimize — strip repeated stable context before model calls
        self.auto_optimize = auto_optimize
        self._stable_context_hashes: set[str] = set()
        # Phase 1.8: budget governor — track cost + retries, enforce limits
        self.max_retries = max_retries
        self.max_cost_per_run = max_cost_per_run
        self._session_cost: float = 0.0
        self._retry_count: int = 0
        self.task_span_id = f"span_task_{uuid4().hex[:8]}"
        self.events: list[dict[str, Any]] = []
        self.trace_path: Path | None = None
        self._ended = False
        self._context_hashes: dict[str, int] = {}

    def check_budget(self) -> tuple[bool, str]:
        """Phase 1.8: Check if session cost or retry count exceeds configured limits.
        Returns (allowed, reason). Call before each model/tool invocation."""
        if self.max_cost_per_run is not None and self._session_cost >= self.max_cost_per_run:
            return False, f"Budget exceeded: ${self._session_cost:.4f} >= ${self.max_cost_per_run:.4f} limit"
        if self.max_retries is not None and self._retry_count >= self.max_retries:
            return False, f"Retry limit reached: {self._retry_count} >= {self.max_retries} max retries"
        return True, ""

    def record_cost(self, cost_dollars: float) -> None:
        """Phase 1.8: Accumulate cost for budget tracking."""
        self._session_cost += cost_dollars

    def record_retry(self) -> None:
        """Phase 1.8: Increment retry counter."""
        self._retry_count += 1

    def register_stable_context(self, context_hash: str) -> bool:
        """Phase 1.7: Register a stable context hash. Returns True if this is a repeat (can be skipped)."""
        if context_hash in self._stable_context_hashes:
            return True  # repeated — can be optimized away
        self._stable_context_hashes.add(context_hash)
        return False  # first time seen

    def __enter__(self) -> "AgentRuntimeTracer":
        self.start_task()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self._ended:
            self.end_task(status="failed" if exc else "completed")
        self.write()

    def add_event(
        self,
        event_type: str,
        span_id: str,
        name: str,
        attributes: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        parent_span_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_id": f"evt_{uuid4().hex[:12]}",
            "task_id": self.task_id,
            "timestamp": timestamp or utc_now(),
            "event_type": event_type,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "name": name,
            "attributes": redact_value(attributes or {}),
            "payload": redact_value(payload or {}),
        }
        self.events.append(event)
        return event

    def start_task(self) -> None:
        if self.events:
            return
        self.add_event(
            event_type="task_start",
            span_id=self.task_span_id,
            name="task_start",
            payload={
                "goal": self.task_name,
                "agent_type": self.agent_type,
                "budget_dollars": self.budget_dollars,
                "latency_slo_seconds": self.latency_slo_seconds,
            },
        )

    def end_task(self, status: str = "completed", summary: str | None = None) -> None:
        self.add_event(
            event_type="task_end",
            span_id=self.task_span_id,
            name="task_end",
            payload={
                "status": status,
                "summary": summary or f"SDK task {status}.",
            },
        )
        self._ended = True

    def model_call(
        self,
        model: str,
        role: str,
        estimated_input_tokens: int = 0,
        expected_output_tokens: int = 0,
        prompt_hash_value: str | None = None,
        name: str = "model_call",
        attributes: dict[str, Any] | None = None,
    ) -> ModelCallSpan:
        return ModelCallSpan(
            tracer=self,
            model=model,
            role=role,
            estimated_input_tokens=estimated_input_tokens,
            expected_output_tokens=expected_output_tokens,
            prompt_hash_value=prompt_hash_value,
            name=name,
            attributes=attributes,
        )

    def tool_call(
        self,
        tool_name: str,
        command: str | None = None,
        risk_level: str = "unknown",
        name: str = "tool_call",
        attributes: dict[str, Any] | None = None,
    ) -> ToolCallSpan:
        return ToolCallSpan(
            tracer=self,
            tool_name=tool_name,
            command=command,
            risk_level=risk_level,
            name=name,
            attributes=attributes,
        )

    def log_model_call(
        self,
        model: str,
        role: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        cost_dollars: float = 0.0,
        status: str = "success",
        prompt_hash_value: str | None = None,
        name: str = "model_call",
    ) -> None:
        span_id = f"span_model_{uuid4().hex[:8]}"
        timestamp = utc_now()
        self.add_event(
            event_type="model_call_start",
            span_id=span_id,
            parent_span_id=self.task_span_id,
            name=name,
            attributes={
                "model": model,
                "role": role,
                "estimated_input_tokens": input_tokens,
                "expected_output_tokens": output_tokens,
                "prompt_hash": prompt_hash_value or "sha256:unknown",
            },
            timestamp=timestamp,
        )
        self.add_event(
            event_type="model_call_end",
            span_id=span_id,
            parent_span_id=self.task_span_id,
            name=f"{name}_end",
            attributes={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_dollars": cost_dollars,
                "status": status,
            },
        )

    def log_tool_call(
        self,
        tool_name: str,
        latency_ms: int,
        command: str | None = None,
        status: str = "success",
        exit_code: int | None = 0,
        risk_level: str = "unknown",
        name: str = "tool_call",
    ) -> None:
        span_id = f"span_tool_{uuid4().hex[:8]}"
        self.add_event(
            event_type="tool_call_start",
            span_id=span_id,
            parent_span_id=self.task_span_id,
            name=name,
            attributes={
                "tool_name": tool_name,
                "command": command,
                "risk_level": risk_level,
            },
        )
        self.add_event(
            event_type="tool_call_end",
            span_id=span_id,
            parent_span_id=self.task_span_id,
            name=f"{name}_end",
            attributes={
                "latency_ms": latency_ms,
                "status": status,
                "exit_code": exit_code,
            },
        )

    def estimate_repeated_tokens(self, context_hash_value: str, size_tokens: int) -> int:
        previous_size = self._context_hashes.get(context_hash_value)
        self._context_hashes[context_hash_value] = size_tokens
        return min(previous_size, size_tokens) if previous_size is not None else 0

    def log_context_snapshot(
        self,
        size_tokens: int,
        repeated_tokens_estimate: int | None = None,
        context_kind: str = "unknown",
        context_hash_value: str | None = None,
        context_id: str | None = None,
    ) -> None:
        resolved_hash = context_hash_value or f"sha256:context-{uuid4().hex[:12]}"
        repeated = (
            repeated_tokens_estimate
            if repeated_tokens_estimate is not None
            else self.estimate_repeated_tokens(resolved_hash, size_tokens)
        )
        self.add_event(
            event_type="context_snapshot",
            span_id=f"span_ctx_{uuid4().hex[:8]}",
            parent_span_id=self.task_span_id,
            name="context_snapshot",
            attributes={
                "context_id": context_id or f"ctx_{uuid4().hex[:12]}",
                "size_tokens": size_tokens,
                "repeated_tokens_estimate": repeated,
                "context_kind": context_kind,
                "context_hash": resolved_hash,
            },
        )

    def log_cache_event(
        self,
        reusable_tokens_estimate: int,
        cache_hit: bool = False,
        cache_kind: str = "prefix_or_kv_estimate",
        reuse_reason: str = "SDK estimated reusable context",
    ) -> None:
        self.add_event(
            event_type="cache_event",
            span_id=f"span_cache_{uuid4().hex[:8]}",
            parent_span_id=self.task_span_id,
            name="cache_event",
            attributes={
                "cache_kind": cache_kind,
                "cache_hit": cache_hit,
                "reusable_tokens_estimate": reusable_tokens_estimate,
                "reuse_reason": reuse_reason,
            },
        )

    def to_trace(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "task": {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "goal": self.task_name,
                "agent_type": self.agent_type,
                "budget_dollars": self.budget_dollars,
                "latency_slo_seconds": self.latency_slo_seconds,
            },
            "events": self.events,
        }

    def write(self) -> TraceWriteResult:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_path = self.trace_dir / f"{self.task_id}.json"
        self.trace_path.write_text(json.dumps(self.to_trace(), indent=2), encoding="utf-8")
        return TraceWriteResult(task_id=self.task_id, trace_path=self.trace_path)

    def upload(self, base_url: str = "http://localhost:8000/api") -> dict:
        result = self.write()
        return AgentRuntimeClient(base_url).import_trace_file(result.trace_path)
