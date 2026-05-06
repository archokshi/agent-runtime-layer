# BUILD_PLAN.md

## Build Goal
Create **Agent Runtime Layer v0.1**: a local-first trace profiler for coding agents.

## Phase 1: Repo Scaffold
Create:
- `backend/`
- `frontend/`
- `packages/sdk-python/`
- `examples/sample-traces/`
- `docs/`
- `docker-compose.yml`
- `README.md`

## Phase 2: Trace Schema
Define JSON schema and database tables for:
- projects
- tasks
- events
- context_snapshots
- analysis_reports
- recommendations

## Phase 3: Backend API
Implement FastAPI endpoints:
- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/events`
- `POST /api/traces/import`
- `GET /api/tasks/{task_id}/events`
- `GET /api/tasks/{task_id}/analysis`
- `GET /api/tasks/{task_id}/blueprint`

## Phase 4: Analyzer Engine
Implement:
- latency breakdown
- cost breakdown
- model/tool split
- repeated-context estimate
- retry/loop detection
- bottleneck classifier
- Silicon Blueprint preview generator

## Phase 5: Frontend Dashboard
Implement:
- task list
- task summary page
- execution timeline
- model/tool call table
- execution graph
- bottleneck report
- repeated-context card
- Silicon Blueprint preview

## Phase 6: SDK and CLI
Implement:
- Python SDK for trace events
- CLI to import trace JSON
- CLI to run a wrapped command if feasible

## Phase 7: Sample Data
Create 3 sample traces:
- successful coding-agent task
- slow tool-heavy task
- repeated-context-heavy task

## Phase 8: Tests
Add tests for:
- event ingestion
- task creation
- analysis calculation
- blueprint recommendation generation

## Phase 9: Demo
README must include:
- setup
- run backend
- run frontend
- import sample trace
- view dashboard
