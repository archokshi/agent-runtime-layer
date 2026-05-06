# API_SPEC.md

## Backend API
Use FastAPI. Return JSON. Keep APIs simple and local-first.

## Endpoints

### Health
`GET /api/health`

Response:
```json
{"status":"ok"}
```

### Create Task
`POST /api/tasks`

Request:
```json
{
  "project_id": "default",
  "goal": "Fix failing auth.test.ts",
  "agent_type": "coding_agent",
  "budget_dollars": 1.0,
  "latency_slo_seconds": 600
}
```

Response:
```json
{"task_id":"task_001"}
```

### List Tasks
`GET /api/tasks`

### Get Task
`GET /api/tasks/{task_id}`

### Add Event
`POST /api/events`

Request: one event object matching TRACE_SCHEMA.md.

### Import Trace
`POST /api/traces/import`

Request:
```json
{
  "project_id": "default",
  "task": {...},
  "events": [...]
}
```

### Get Events
`GET /api/tasks/{task_id}/events`

### Export OpenTelemetry JSON
`GET /api/tasks/{task_id}/otel`

Response:
OpenTelemetry-style JSON with `resourceSpans`, resource metadata, span IDs, parent span IDs, attributes, and status.

### Import OpenTelemetry JSON
`POST /api/traces/import/otel`

Request:
OpenTelemetry-style JSON with `resourceSpans`.

Response:
```json
{"task_id":"task_001","event_count":12}
```

### Get Analysis
`GET /api/tasks/{task_id}/analysis`

### Get Blueprint Preview
`GET /api/tasks/{task_id}/blueprint`

### Get Optimization Recommendations
`GET /api/tasks/{task_id}/optimizations`

Response:
```json
{
  "task_id": "task_001",
  "recommendations": [
    {
      "recommendation_id": "task_001:opt-tool-wait",
      "category": "tool_scheduling",
      "title": "Reduce blocking tool wait",
      "evidence": "Tool execution consumed 18000ms of 30000ms total task time.",
      "action": "Batch independent terminal/file operations and schedule model planning around long-running tools.",
      "estimated_time_savings_ms": 4500,
      "estimated_cost_savings_dollars": 0.0,
      "confidence": 0.78,
      "metrics": {}
    }
  ]
}
```

### Get Validation Report
`GET /api/tasks/{task_id}/validation`

Response:
```json
{
  "task_id": "task_001",
  "metadata": {
    "benchmark_name": "swebench-lite-mini",
    "benchmark_task_id": "django__django-0001",
    "repo_name": "django/django",
    "issue_id": "0001",
    "agent_name": "custom-langgraph-agent",
    "baseline_or_optimized": "optimized",
    "task_success": true,
    "tests_passed": 42,
    "tests_failed": 0,
    "patch_generated": true,
    "files_changed_count": 2,
    "retry_count": 0,
    "before_after_pair_id": "pair_swebench_001"
  },
  "comparison": {
    "before_after_pair_id": "pair_swebench_001",
    "baseline_task_id": "task_swebench_baseline_001",
    "optimized_task_id": "task_swebench_optimized_001",
    "repeated_input_token_reduction_percent": 75.0,
    "estimated_cost_reduction_percent": 60.0,
    "latency_change_percent": -33.3,
    "success_preserved": true
  }
}
```

## Analyzer Contract
The analyzer should be deterministic. Given the same event list, it must return the same report.

## Frontend Pages
- `/` task list
- `/tasks/[task_id]` task dashboard
- `/import` sample trace import page if useful

## Dashboard Sections
- Task summary
- Timeline
- Execution graph
- Event table
- Bottleneck report
- Repeated-context report
- Optimization recommendations
- Validation report
- Silicon Blueprint preview
