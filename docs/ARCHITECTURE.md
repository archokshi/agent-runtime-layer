# Architecture

Agent Runtime Layer is a self-hosted profiler for coding-agent workloads.

## Components

```text
Trace sources
  - sample traces
  - CLI command wrapper
  - Python SDK
  - coding-agent adapters
        |
        v
FastAPI backend
  - trace import
  - SQLite persistence
  - deterministic analysis
  - optimization reports
  - workload reports
        |
        v
Next.js dashboard
  - overview
  - runs
  - task detail
  - benchmarks
  - workload report
  - advanced evidence views
```

## Backend

The backend is a FastAPI service under `backend/app`.

Primary responsibilities:

- import Agent Runtime traces
- export/import OpenTelemetry-style traces
- persist tasks and events in SQLite
- compute latency, cost, token, retry, and bottleneck metrics
- generate optimization recommendations
- generate context optimization reports
- generate workload reports

## Frontend

The dashboard is a Next.js app under `frontend/src`.

Primary pages:

- `/` overview and golden demo entry
- `/runs` task list
- `/tasks/<task_id>` task detail
- `/benchmarks` benchmark evidence
- `/workload-report` evaluation and recommendation report
- `/advanced` advanced evidence entry points

## SDK

The Python SDK lives in `packages/sdk-python`.

It can:

- import trace JSON
- capture local command traces
- instrument custom agent model/tool/context events
- wrap supported coding-agent CLI flows

## Storage

SQLite is the default local store. Runtime databases and generated artifacts are ignored by Git.

## Design Principle

Agent Runtime Layer separates:

- measured evidence
- estimated opportunity
- inferred recommendation

The UI and reports should not claim measured performance where only estimates exist.

