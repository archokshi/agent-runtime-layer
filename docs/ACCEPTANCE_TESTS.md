# ACCEPTANCE_TESTS.md

## Local Run
- `docker compose up` starts backend and frontend.
- Frontend opens without errors.
- Backend docs are available at `/docs`.

## Trace Import
- Importing a sample trace creates one task.
- Imported events appear in correct timestamp order.
- Task summary displays total time, event count, model calls, and tool calls.

## Analysis
For a sample trace, dashboard must show:
- total duration
- model time
- tool time
- orchestration/idle estimate
- input/output token totals where available
- estimated cost where model pricing is provided
- repeated-context estimate
- bottleneck classification

## Execution Graph
- Model calls and tool calls render as graph nodes.
- Dependencies render as edges.
- Clicking a node shows event details.

## Silicon Blueprint Preview
For each task, generate recommendations such as:
- persistent KV/prefix cache recommended
- tool-wait-aware scheduler recommended
- warm context tier recommended
- prefill/decode split candidate
Only show recommendations when supported by trace metrics.

## Security
- Obvious secrets such as strings matching `sk-`, `api_key=`, `password=`, `.env` values are redacted before storage.
- Raw file contents are optional and can be disabled.

## Tests
- Backend tests pass.
- Analyzer tests pass.

## v0.5 Benchmark Suite Integration
- `POST /api/benchmarks/runs` stores a SWE-bench, Aider, OpenHands, or custom benchmark record.
- `GET /api/benchmarks/runs` lists persisted benchmark records.
- `GET /api/benchmarks/summary` returns run count, task count, suite counts, trace completion rate, task success rate, and actionable recommendation rate.
- `/benchmarks` renders benchmark suite coverage.
- `/platform` includes benchmark suite coverage.
- UI and API copy must not claim official SWE-bench/OpenHands/Aider scores unless the run record is marked and verified as official.
