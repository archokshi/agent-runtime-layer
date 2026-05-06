# Changelog

## Unreleased - Developer Preview Readiness

- Added one-click golden demo from the homepage.
- Added bundled golden coding-agent trace.
- Added public README focused on quickstart, demo, value, validation, privacy, and limitations.
- Added `LICENSE`, `.env.example`, `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md`.
- Added GitHub issue templates, pull request template, and CI workflow.
- Added public docs for quickstart, architecture, limitations, and release checklist.
- Expanded `.gitignore` to exclude secrets, SQLite databases, cache folders, local traces, and generated test artifacts.

## Phase 1.011

- Added formal Phase 1 exit package generation.
- Added `POST /api/phase-1-exit/generate`.
- Added `GET /api/phase-1-exit`.
- Added `GET /api/phase-1-exit/{package_id}`.
- Added `GET /api/phase-1-exit/{package_id}/export.md`.
- Added SQLite persistence for Phase 1.011 packages.
- Added `/phase-1-exit` dashboard.
- Added Phase 1 Exit navigation link.
- Package includes Workload Evaluation Package, Workload Recommendation Package, metric quality scorecard, architecture readiness, Phase 1.5 hardware test plan, Phase 2 architecture signals, and do-not-do-yet list.
- Uses existing local evidence only; does not run new SWE-bench, OpenHands, vLLM, SGLang, Dynamo, or hardware tests.
- Does not implement hardware simulation, RTL, FPGA, ASIC, or a new runtime feature layer.

## v5.0

- Added Agentic Inference Platform overview.
- Added `GET /api/platform/summary`.
- Added `/platform` dashboard.
- Added platform metric cards, module coverage, readiness scores, and end-to-end runbook.
- Added readiness categories for optimization, backend validation, hardware-aware analysis, Silicon Blueprint, and measured benchmark work.
- Added measured validation experiment storage.
- Added `POST /api/validation/experiments`.
- Added `GET /api/validation/experiments`.
- Added projected-vs-measured validation records to the platform summary and dashboard.
- Added Platform navigation link.
- Added v5.0 backend test coverage and acceptance criteria.
- Local-first only; does not implement cloud SaaS, production auth, billing, real backend control, hardware simulation, or measured improvement claims without benchmark evidence.

## v0.5 Benchmark Suite Integration

- Added first-class benchmark suite records under v0.5 validation.
- Added `POST /api/benchmarks/runs`.
- Added `GET /api/benchmarks/runs`.
- Added `GET /api/benchmarks/summary`.
- Added SQLite persistence for SWE-bench, Aider, OpenHands, and custom benchmark records.
- Added benchmark summary metrics for trace completion, task success, actionable recommendations, retries, duration, and cost.
- Added `/benchmarks` dashboard page.
- Added Benchmark navigation link.
- Added benchmark suite coverage to `/platform`.
- Does not automatically download SWE-bench, install OpenHands, execute external benchmark harnesses, or claim official benchmark scores from smoke/imported records.

## v4.5

- Added replay scenario selection for all five scenarios.
- Added dashboard checkboxes for persistent prefix cache, tool-wait scheduler, prefill/decode split, warm context tier, and KV/context compression.
- Added replay comparison summary for best duration, cost, and prefill scenario.
- Added projection confidence reason per scenario.
- Added real-backend-validation flag per scenario.
- Added validation evidence checklist per scenario.
- Added `GET /api/replays/{replay_id}/export.md`.
- Added replay Markdown export.
- Added v4.5 acceptance tests and validation report.
- Remains projection-only and does not claim measured backend or hardware speedups.

## v4.0

- Added Trace Replay Simulator.
- Added `POST /api/blueprints/{blueprint_id}/simulate`.
- Added `GET /api/blueprints/{blueprint_id}/replays`.
- Added `GET /api/replays/{replay_id}`.
- Added SQLite persistence for trace replay reports.
- Added rule-based scenarios for persistent prefix cache, tool-wait scheduler, prefill/decode split, warm context tier, and KV/context compression.
- Added projected baseline vs scenario metrics for duration, model time, tool time, idle time, input tokens, cost, prefill time, and queue pressure.
- Added dashboard Trace Replay Simulator section on `/blueprints`.
- Added backend acceptance coverage for replay generation and persistence.
- Does not perform real KV-cache control, live backend routing, production scheduling, hardware simulation, RTL, ASIC design, FPGA output, or measured hardware improvement.

## v3.5

- Added Silicon Blueprint Engine report generation.
- Added `POST /api/blueprints/generate`.
- Added `GET /api/blueprints`.
- Added `GET /api/blueprints/{blueprint_id}`.
- Added SQLite persistence for blueprint architecture reports.
- Added workload profile aggregation across imported traces.
- Added bottleneck map aggregation from trace analysis and imported hardware telemetry.
- Added memory hierarchy recommendations, hardware primitive rankings, backend/runtime recommendations, benchmark proposals, and report limitations.
- Added `/blueprints` dashboard page with Generate Blueprint button.
- Added v3.5 backend acceptance test.
- Added validation coverage summary to blueprint reports.
- Added Markdown export endpoint at `GET /api/blueprints/{blueprint_id}/export.md`.
- Added dashboard validation coverage and Export Markdown action.
- Added broader local validation report documentation.
- Does not generate ASIC design, RTL, FPGA output, hardware simulation, or measured hardware improvement.

## v3.0

- Added imported hardware/backend telemetry schema.
- Added `POST /api/tasks/{task_id}/telemetry/import`.
- Added `GET /api/tasks/{task_id}/hardware-analysis`.
- Added SQLite persistence for telemetry samples and hardware analysis reports.
- Added timestamp correlation between telemetry samples and model/tool event windows.
- Added hardware bottleneck classification for queue saturation, memory pressure, low cache hit rate, prefill pressure, decode pressure, and GPU underutilization.
- Added dashboard Hardware-Aware Runtime report.
- Added sample telemetry fixture and v3.0 tests.
- Added GPU-underutilized queue telemetry fixture and validation.
- Does not poll live GPUs, perform full cluster monitoring, or simulate hardware.

## v2.5

- Added Backend-Aware Runtime hint generation.
- Added `POST /api/tasks/{task_id}/backend-hints`.
- Added `GET /api/tasks/{task_id}/backend-hints`.
- Added persisted backend-aware reports.
- Added backend registry, model-call profiles, prefix-overlap estimates, cache-locality classification, and prefill/decode classification.
- Added dashboard Backend-Aware Runtime report with Generate Backend Hints button.
- Added v2.5 acceptance tests.
- Added controlled backend queue-pressure validation trace.
- Does not call real vLLM, SGLang, LMCache, Dynamo, or perform production load balancing.

## v2.0

- Added local deterministic Runtime Scheduler simulation.
- Added `POST /api/tasks/{task_id}/schedule`.
- Added `GET /api/tasks/{task_id}/schedule`.
- Added persisted scheduler reports.
- Added task priority field alongside existing budget and latency SLO fields.
- Added scheduler decisions for tool wait, orchestration idle gaps, retry throttling, SLO risk, and budget gating.
- Added dashboard Runtime Scheduler report with Run Scheduler Tick button.
- Added v2.0 acceptance tests.
- Does not implement a production multi-agent scheduler, backend-aware routing, or hardware simulation.

## v1.5

- Added Optimization Executor for repeated-context traces.
- Added `POST /api/tasks/{task_id}/optimize-context`.
- Added `GET /api/tasks/{task_id}/optimized-context`.
- Added stable context block detection, dynamic context separation, context fingerprinting, and optimized prompt package generation.
- Added persisted context optimization reports.
- Added dashboard Optimization Executor report with Run Optimize Context button.
- Added controlled repeated-context sample trace.
- Added post-v1 acceptance tests.
- Uses prefix-cache-ready wording and does not claim real KV-cache control.
- Added v1.5 executor documentation and real OpenAI before/after validation helper.
- Ran controlled real OpenAI v1.5 before/after validation with 33.73% measured input-token reduction and task success preserved.

## v1.0

- Added deterministic optimization recommendation generation.
- Added `GET /api/tasks/{task_id}/optimizations`.
- Added dashboard cards for top optimization recommendations.
- Recommendations include trace evidence, concrete action, estimated time savings, estimated cost savings, and confidence.
- Added rules for repeated context, tool wait, model routing, retry loops, and orchestration idle time.
- Added backend tests for repeated-context and tool-wait recommendations.
- Added v1.0 validation metadata for real-world coding-agent workloads.
- Added `GET /api/tasks/{task_id}/validation`.
- Added dashboard validation section with task outcome and before/after comparison.
- Added sample validation traces for SWE-bench-style baseline/optimized comparison and Aider-style retry loops.
- Added `docs/V1_VALIDATION_PLAN.md`.

## v0.5

- Added OpenTelemetry-style JSON export endpoint at `GET /api/tasks/{task_id}/otel`.
- Added OpenTelemetry-style JSON import endpoint at `POST /api/traces/import/otel`.
- Added SDK conversion helpers for Agent Runtime trace JSON to/from OTEL-style JSON.
- Added CLI commands `export-otel`, `import-otel`, `convert-otel`, and `convert-from-otel`.
- Preserves task graph structure with `traceId`, `spanId`, and `parentSpanId`.
- Emits resource metadata, span attributes, and span status.
- Keeps the existing Agent Runtime trace schema as the canonical local format.
- Added backend and SDK tests for OTEL export/import round trips.

## v0.4.1

- Parsed Aider stdout model metadata into synthetic `model_call_start` and `model_call_end` events.
- Captures Aider model name, input tokens, output tokens, and message cost when Aider prints usage lines.
- Validated with a live Aider/OpenAI run where backend analysis reported one model call and real token/cost metadata.

## v0.4

- Added first coding-agent integration adapter for Aider.
- Added `agent-runtime integrate aider`.
- Captures Aider CLI terminal output, duration, exit code, and Git file metadata.
- Writes/imports Aider-shaped traces through the existing backend.
- Added Aider integration docs and mock validation flow.
- Added tests for terminal and file-event trace mapping.

## v0.3

- Added `AgentRuntimeTracer` for custom Python agent instrumentation.
- Added model-call and tool-call context managers.
- Added `log_model_call()`, `log_tool_call()`, `log_context_snapshot()`, and `log_cache_event()`.
- Added prompt/context hash helpers.
- Added token/cost metadata support and a simple cost estimator.
- Added repeated-context estimation for repeated context hashes.
- Added a custom-agent SDK demo script.
- Added SDK tests for generated model/tool/context/cache traces.

## v0.2

- Added real local trace capture with `agent-runtime trace`.
- Captures command start/end, duration, exit code, stdout/stderr summaries, terminal events, and task lifecycle events.
- Writes trace JSON to `.agent-runtime/traces/<task_id>.json`.
- Added optional `--upload`, `--capture-diff`, `--capture-full-logs`, and `--project` flags.
- Added local redaction for stdout/stderr before writing trace JSON.
- Added SDK tests for successful commands, failing commands, and secret redaction.

## v0.1

- Added sample trace import, SQLite persistence, analyzer, Silicon Blueprint Preview, dashboard, SDK import client, Docker Compose, and backend tests.
