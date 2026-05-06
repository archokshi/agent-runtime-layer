# TRACE_SCHEMA.md

## Purpose
The trace schema records the full execution of a coding-agent task: model calls, tool calls, context snapshots, file/terminal events, cache hints, errors, and final outputs.

## Core Concepts

### Project
A logical workspace or product using Agent Runtime Layer.

### Task
One user goal handled by an agent, such as “Fix failing auth.test.ts”.

### Event
A timestamped observation within the task. Events can represent model calls, tool calls, context snapshots, file changes, terminal output, cache hints, or recommendations.

### Analysis Report
Derived metrics and bottleneck classifications produced from task events.

### Silicon Blueprint Preview
A human-readable report that maps observed bottlenecks to possible hardware/system architecture implications.

## Required Event Fields
```json
{
  "event_id": "evt_001",
  "task_id": "task_001",
  "timestamp": "2026-05-03T10:01:00.000Z",
  "event_type": "model_call_start",
  "span_id": "span_model_001",
  "parent_span_id": "span_task_001",
  "name": "planner_model_call",
  "attributes": {},
  "payload": {}
}
```

## Event Types

### task_start
Required payload:
```json
{
  "goal": "Fix failing auth.test.ts",
  "agent_type": "coding_agent",
  "budget_dollars": 1.0,
  "latency_slo_seconds": 600
}
```

### task_end
Required payload:
```json
{
  "status": "completed",
  "summary": "Fixed test failure by updating token parsing logic."
}
```

### model_call_start
Required attributes:
```json
{
  "model": "gpt-5-codex",
  "role": "planner",
  "estimated_input_tokens": 12000,
  "expected_output_tokens": 600,
  "prompt_hash": "sha256:..."
}
```

### model_call_end
Required attributes:
```json
{
  "input_tokens": 12000,
  "output_tokens": 540,
  "latency_ms": 4200,
  "cost_dollars": 0.055,
  "status": "success"
}
```

### tool_call_start
Required attributes:
```json
{
  "tool_name": "terminal",
  "command": "pytest tests/test_auth.py",
  "risk_level": "medium"
}
```

### tool_call_end
Required attributes:
```json
{
  "latency_ms": 18000,
  "status": "failed",
  "exit_code": 1
}
```

### context_snapshot
Required attributes:
```json
{
  "context_id": "ctx_001",
  "size_tokens": 18000,
  "repeated_tokens_estimate": 7000,
  "context_kind": "repo_summary_plus_test_log"
}
```

### cache_event
Required attributes:
```json
{
  "cache_kind": "prefix_or_kv_estimate",
  "cache_hit": false,
  "reusable_tokens_estimate": 8000,
  "reuse_reason": "repeated repo summary and tool schema"
}
```

### file_event
Required attributes:
```json
{
  "operation": "read|write|diff",
  "path": "src/auth.ts",
  "bytes": 3812,
  "content_stored": false
}
```

### terminal_event
Required attributes:
```json
{
  "command": "pytest tests/test_auth.py",
  "duration_ms": 18000,
  "exit_code": 1,
  "stdout_preview": "...",
  "stderr_preview": "..."
}
```

### error_event
Required attributes:
```json
{
  "error_type": "tool_failure",
  "message": "pytest failed",
  "recoverable": true
}
```

## Derived Metrics
The analyzer should compute:
- total_task_duration_ms
- model_time_ms
- tool_time_ms
- model_call_count
- tool_call_count
- total_input_tokens
- total_output_tokens
- estimated_total_cost_dollars
- repeated_context_tokens_estimate
- repeated_context_percent
- cache_reuse_opportunity_percent
- retry_count
- bottleneck_category

## Bottleneck Categories
- repeated_context
- tool_wait
- model_latency
- context_growth
- retry_loop
- orchestration_idle
- mixed

## OpenTelemetry Compatibility

The Agent Runtime trace schema remains the canonical local format. v0.5 adds an OpenTelemetry-style compatibility bridge.

Exported OTEL JSON includes:
- `resourceSpans`
- resource attributes for `service.name`, `service.version`, `arl.project_id`, `arl.task_id`, `arl.task.goal`, and `arl.task.agent_type`
- one span per Agent Runtime event
- deterministic `traceId` derived from task ID
- deterministic `spanId` derived from the Agent Runtime `span_id`
- `parentSpanId` derived from `parent_span_id`
- event metadata in span attributes
- original event `attributes` and `payload` preserved as JSON attributes
- span `status` derived from event status fields where available

OTEL import is best-effort and intended for interoperability. Imported OTEL traces are converted back into Agent Runtime events before storage and analysis.
