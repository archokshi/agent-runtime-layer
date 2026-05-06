# Agent Runtime Layer + Agent Silicon Blueprint — Version Roadmap

## 1. Product Thesis

Agent Runtime Layer is the software runtime/profiler/optimizer that traces and improves agent workflows.

Agent Silicon Blueprint is the hardware/system architecture output derived from real agent traces.

The key principle:

Runtime first as the measurement and learning engine. Silicon Blueprint second as the architecture and acceleration engine.

## 2. Current Status

Current implemented version: v5.0

Phase 1.011 status:
- formal Phase 1 exit package exists as a generated artifact, not a new product version
- `POST /api/phase-1-exit/generate` generates the Workload Evaluation + Recommendation Package
- `GET /api/phase-1-exit` lists generated packages
- `GET /api/phase-1-exit/{package_id}` returns a package
- `GET /api/phase-1-exit/{package_id}/export.md` exports Markdown
- `/phase-1-exit` dashboard renders evaluation, recommendations, metric quality, architecture readiness, Phase 1.5 test plan, and Phase 2 signals
- Phase 1.011 uses existing local evidence only and does not run new SWE-bench, OpenHands, vLLM, SGLang, Dynamo, or hardware tests
- Phase 1.011 does not build hardware simulation, RTL, FPGA, ASIC, or a new runtime feature layer

v0.1 status:
- sample trace import works
- SQLite persistence works
- deterministic analyzer works
- Silicon Blueprint Preview works
- Next.js dashboard works
- Docker local deployment works

v0.2 status:
- real local command trace capture works
- successful commands generate trace JSON
- failing commands generate failed trace JSON
- command duration and exit code capture works
- stdout/stderr summary capture works
- local stdout/stderr redaction works
- generated traces import into backend
- dashboard displays generated local command traces

v0.3 status:
- Python SDK tracer works
- model-call context manager works
- tool-call context manager works
- context snapshot logging works
- cache event logging works
- prompt/context hash helpers work
- cost estimator works
- repeated-context estimation works
- SDK-generated traces import into backend
- dashboard displays SDK-generated model/tool/context traces

v0.4 status:
- Aider integration adapter exists
- `agent-runtime integrate aider` works
- Aider-shaped terminal events are captured
- Aider stdout model metadata is parsed into synthetic model-call events
- Aider token and cost metadata are reflected in analysis
- Git file metadata events are captured
- generated integration traces import into backend
- dashboard displays generated integration traces
- local mock validation works without Aider credentials
- live Aider/OpenAI validation works with provider credentials

v0.5 status:
- OpenTelemetry-style JSON export works
- OpenTelemetry-style JSON import works
- `trace_id`, `span_id`, `parent_span_id`, attributes, status, and resource metadata are emitted
- exported traces preserve task graph structure
- imported OTEL traces can be analyzed by the existing analyzer
- existing Agent Runtime trace schema remains backward compatible
- benchmark suite validation is now first-class in v0.5
- `POST /api/benchmarks/runs` stores SWE-bench/Aider/OpenHands/custom benchmark records
- `GET /api/benchmarks/runs` lists benchmark records
- `GET /api/benchmarks/summary` summarizes benchmark task count, trace completion, success rate, and actionable recommendation rate
- `/benchmarks` dashboard renders benchmark validation coverage
- `/platform` includes benchmark suite coverage

v1.0 status:
- deterministic optimization recommendation endpoint works
- dashboard shows top optimization recommendations
- recommendations include evidence, action, estimated time savings, estimated cost savings, and confidence
- repeated-context, tool-wait, model-routing, retry-loop, and orchestration-idle recommendation rules exist
- recommendations are backed by analyzer metrics
- real-world validation metadata is supported
- before/after validation comparison works
- validation dashboard section exists
- SWE-bench-style baseline/optimized sample traces exist
- Aider-style retry-loop sample trace exists
- real Aider/OpenAI failing-pytest validation has been run locally

v1.0/v1.5 remaining real-workload validation:
- Track A official SWE-bench Lite/Verified mini-suite has not been run yet
- Track C controlled real OpenAI before/after repeated-context experiment has been run once for v1.5
- broader Track C validation across multiple coding tasks is still pending
- current Track A support is validation scaffolding plus sample traces, not official benchmark execution

v1.5 status:
- `POST /api/tasks/{task_id}/optimize-context` generates a context optimization report
- `GET /api/tasks/{task_id}/optimized-context` returns the persisted report
- stable context block detection works on controlled repeated-context traces
- dynamic context separation works on controlled repeated-context traces
- optimized prompt/context package artifact is generated
- estimated repeated-token, cost, and prefill reductions are reported
- dashboard shows Optimization Executor report and Run Optimize Context button
- v1.5 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- v1.5 executor notes and no-overclaiming guidance are documented in `docs/V1_5_OPTIMIZATION_EXECUTOR.md`
- real OpenAI before/after validation helper exists in `examples/v1_5_controlled_openai_experiment.py`
- controlled real OpenAI v1.5 validation run completed on `2026-05-04`
- validation run imported `task_v1_5_real_context_baseline_203c3d6d` and `task_v1_5_real_context_optimized_203c3d6d`
- measured OpenAI input tokens dropped from 424 to 281, a 33.73% reduction
- paired validation report shows estimated cost reduction of 10.67% and task success preserved
- baseline optimizer report shows 30.9% estimated input-token, cost, and prefill reduction

v2.0 status:
- `POST /api/tasks/{task_id}/schedule` runs a local deterministic scheduler simulation
- `GET /api/tasks/{task_id}/schedule` returns the persisted scheduler report
- task priority, budget, and latency SLO fields are supported
- scheduler decisions cover tool wait, idle gaps, retry throttling, SLO risk, and budget gating
- scheduler metrics include naive vs scheduled estimated duration, idle reduction, and simulated tasks/hour
- dashboard shows Runtime Scheduler report and Run Scheduler Tick button
- v2.0 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- v2.0 is not a production multi-agent scheduler, backend-aware router, or hardware simulator

v2.5 status:
- `POST /api/tasks/{task_id}/backend-hints` generates backend-agnostic cache/routing hints
- `GET /api/tasks/{task_id}/backend-hints` returns the persisted backend-aware report
- backend registry exists with default and prefix-cache-capable backend classes
- model-call profiling works
- prefix-overlap estimates are calculated from repeated context/cache opportunity metrics
- prefill/decode classification works
- cache-locality classification works
- queue-depth hints work on `examples/sample-traces/v2_5_backend_queue_pressure.json`
- dashboard shows Backend-Aware Runtime report and Generate Backend Hints button
- v2.5 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- v2.5 does not call real vLLM, SGLang, LMCache, Dynamo, or perform production load balancing

v3.0 status:
- `POST /api/tasks/{task_id}/telemetry/import` imports hardware/backend telemetry samples
- `GET /api/tasks/{task_id}/hardware-analysis` returns a correlated hardware-aware report
- telemetry samples are persisted in SQLite
- telemetry timestamps are correlated with model/tool event windows
- bottleneck classifier detects queue saturation, memory pressure, cache miss pressure, prefill bottlenecks, decode bottlenecks, and GPU underutilization
- dashboard shows Hardware-Aware Runtime report
- sample telemetry fixture exists in `examples/sample-telemetry/v3_0_prefill_queue_pressure.json`
- GPU-underutilized validation fixture exists in `examples/sample-telemetry/v3_0_gpu_underutilized_queue.json`
- v3.0 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- v3.0 uses imported telemetry only; no live GPU polling, full cluster monitoring, or hardware simulation

v3.5 status:
- `POST /api/blueprints/generate` generates a Silicon Blueprint architecture report from imported traces
- `GET /api/blueprints` lists persisted blueprint reports
- `GET /api/blueprints/{blueprint_id}` returns a persisted report
- workload profile aggregation works across selected or all local tasks
- bottleneck map combines trace analyzer categories and imported hardware telemetry bottlenecks
- memory hierarchy recommendations are generated with rule-based evidence
- hardware primitive rankings are generated with rule-based scores
- backend/runtime recommendations are generated from trace and telemetry evidence
- benchmark proposals are generated for repeated-context and telemetry-correlated validation
- dashboard `/blueprints` page shows the Silicon Blueprint Engine report
- validation coverage summary shows local trace count, 100-trace target progress, telemetry coverage, and remaining validation items
- Markdown export works with `GET /api/blueprints/{blueprint_id}/export.md`
- v3.5 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- broader local validation report is documented in `docs/V3_5_VALIDATION_REPORT.md`
- v3.5 does not generate ASIC design, RTL, FPGA output, hardware simulation, or measured hardware improvements

v4.0 status:
- `POST /api/blueprints/{blueprint_id}/simulate` generates a rule-based Trace Replay Simulator report
- `GET /api/blueprints/{blueprint_id}/replays` lists persisted replay reports for a blueprint
- `GET /api/replays/{replay_id}` returns a persisted replay report
- replay reports are persisted in SQLite
- default scenarios include persistent prefix cache, tool-wait scheduler, and prefill/decode split
- optional scenarios include warm context tier and KV/context compression
- projected metrics include duration, model time, tool time, idle time, input tokens, cost, prefill time, and queue pressure
- dashboard `/blueprints` page shows Trace Replay Simulator controls and scenario projections
- v4.0 acceptance tests are documented in `docs/ACCEPTANCE_TESTS_POST_V1.md`
- v4.0 is projection-only; it does not perform real KV-cache control, live backend routing, hardware simulation, RTL, ASIC design, or measured hardware improvement

v4.5 status:
- replay scenario selection works for all five scenarios
- dashboard scenario checkboxes support persistent prefix cache, tool-wait scheduler, prefill/decode split, warm context tier, and KV/context compression
- replay reports include confidence reasons, real-backend-validation flags, and validation evidence requirements
- replay comparison summary identifies best duration, cost, and prefill scenarios
- `GET /api/replays/{replay_id}/export.md` exports replay reports as Markdown
- dashboard shows replay comparison summary and Export Replay action
- v4.5 validation report is documented in `docs/V4_5_REPLAY_VALIDATION_REPORT.md`
- v4.5 remains projection-only and does not claim measured backend or hardware speedups

v5.0 status:
- `GET /api/platform/summary` generates a local platform overview
- `POST /api/validation/experiments` stores measured projected-vs-actual validation experiments
- `GET /api/validation/experiments` lists measured validation experiments
- `/platform` dashboard shows traces, analysis, optimization, scheduler, backend hints, hardware telemetry, blueprints, and replay coverage
- project-level readiness scores are generated for optimization, backend validation, hardware-aware analysis, Silicon Blueprint, and measured benchmark work
- end-to-end runbook shows trace -> analyze -> optimize -> schedule -> backend -> telemetry -> blueprint -> replay status
- measured validation records appear in the platform summary and dashboard
- Platform nav link is available in the dashboard header
- v5.0 is local-first only; no cloud SaaS, production auth, billing, real backend control, or hardware simulation

Current local path:
`C:\Users\trive\OneDrive\Desktop\Moonshot\Agentium\Codex_Dev\agent-runtime-layer`

## 3. Version Roadmap Table

| Version | Name | Goal | Primary Output |
|---|---|---|---|
| v0.1 | Sample Trace Profiler | Import sample traces and visualize agent bottlenecks | Working dashboard + Silicon Blueprint Preview |
| v0.2 | Real Local Trace Capture | Capture real command/coding-agent runs locally | CLI-generated trace JSON |
| v0.3 | SDK Model/Tool Instrumentation | Capture model/tool/context events from custom agents | Rich agent trace SDK |
| v0.4 | First Coding-Agent Integration | Integrate with one open-source coding agent | Real coding-agent trace |
| v0.5 | OpenTelemetry Compatibility | Export/import traces in OpenTelemetry-compatible structure | Infra-compatible trace format |
| v1.0 | Optimization Recommendations | Recommend concrete cost/time optimizations | Actionable runtime recommendations |
| v2.0 | Runtime Scheduler | Schedule agent steps based on priority/tool wait/SLO | Scheduler decisions + improved idle time |
| v2.5 | Backend-Aware Runtime | Generate routing/cache hints | Prefix-overlap and cache-locality hints |
| v3.0 | Hardware-Aware Runtime | Correlate traces with hardware telemetry | Task-to-hardware bottleneck map |
| v3.5 | Silicon Blueprint Engine | Generate architecture reports from many traces | Memory hierarchy + primitive ranking |
| v4.0 | Trace Replay Simulator | Simulate hardware/runtime improvements against traces | Architecture simulation results |

## 4. v0.1 Completed Scope

Goal:
Build the first vertical slice.

Implemented:
- FastAPI backend
- SQLite local storage
- task/event/context/analysis/recommendation tables
- sample trace import
- deterministic analyzer
- Silicon Blueprint Preview
- Next.js dashboard
- summary cards
- latency breakdown chart
- execution graph
- event details
- event table
- repeated-context report
- bottleneck report
- Docker packaging
- Python SDK client
- Python CLI trace import

Validation:
- backend tests pass
- FastAPI health works
- frontend build passes
- Docker compose works
- sample trace imports successfully
- dashboard renders task detail page

## 5. v0.2 Real Local Trace Capture

Goal:
Move from imported sample traces to real local trace capture.

User Value:
A developer can run a local command or coding-agent command and automatically generate an Agent Runtime trace.

Example:
```bash
agent-runtime trace --name "local pytest run" -- pytest tests/
```

Features:

- CLI command wrapper
- command start/end capture
- stdout/stderr summary capture
- exit code capture
- duration capture
- task_start/task_end events
- terminal_event generation
- optional full log capture
- optional git diff summary
- optional upload/import into backend

Non-goals:

- no real model-provider integration yet
- no real KV-cache control
- no hardware simulation
- no production auth

Validation:

- successful command creates trace JSON
- failing command creates trace JSON with error status
- generated trace imports into backend
- dashboard displays generated trace
- secret redaction applies to stdout/stderr

Demo Flow:

```bash
agent-runtime trace --name "hello test" -- python -c "print('hello')"
agent-runtime import .agent-runtime/traces/<task_id>.json
```

Codex Prompt:
Implement v0.2 real local trace capture. Add `agent-runtime trace --name "<task name>" -- <shell command>`. Capture command timing, exit code, stdout/stderr summaries, terminal events, task_start, tool_call_start, tool_call_end, task_end, and write trace JSON to `.agent-runtime/traces/`. Add optional flags `--upload`, `--capture-diff`, `--capture-full-logs`, and `--project`.

## 6. v0.3 SDK Model/Tool Instrumentation

Goal:
Capture rich traces from custom agent code.

User Value:
Agent builders can instrument model calls, tool calls, context snapshots, and task lifecycle events directly.

Features:

- Python SDK context managers
- `start_task()`
- `end_task()`
- `log_model_call()`
- `log_tool_call()`
- `log_context_snapshot()`
- `log_cache_event()`
- cost estimator
- prompt/context hash support
- repeated-context estimation

Non-goals:

- no production scheduler
- no real KV-cache manipulation
- no cloud SaaS

Validation:

- demo custom agent produces model/tool/context trace
- trace imports into dashboard
- analyzer calculates model time and tool time
- repeated-context report works on SDK-generated trace

Codex Prompt:
Implement v0.3 Python SDK instrumentation for custom agents. Add context managers for task, model call, tool call, and context snapshot. Include prompt_hash/context_hash fields, token counts, cost metadata, and examples.

## 7. v0.4 First Coding-Agent Integration

Goal:
Integrate with one real open-source coding agent.

Recommended first targets:

- Aider
- OpenHands
- LangGraph-based coding agent

User Value:
Show Agent Runtime Layer working on a real coding-agent workflow.

Features:

- integration adapter
- trace mapping
- demo repo
- before/after trace walkthrough
- integration docs

Non-goals:

- do not start with closed internal Cursor/Claude Code hooks
- do not integrate every agent framework

Validation:

- run one coding-agent task
- capture model/tool/file/terminal events
- dashboard identifies bottleneck
- Silicon Blueprint Preview generates meaningful recommendations

## 8. v0.5 OpenTelemetry Compatibility

Goal:
Make traces interoperable with infrastructure observability tools and make benchmark-suite validation records first-class.

Features:

- trace_id
- span_id
- parent_span_id
- attributes
- status
- resource metadata
- OTEL JSON export
- OTEL import where practical
- SWE-bench/Aider/OpenHands/custom benchmark run records
- benchmark task result metadata
- trace completion rate
- task success rate
- actionable recommendation rate
- benchmark summary API
- benchmark dashboard section

Validation:

- exported traces preserve task graph structure
- imported traces can be analyzed
- schema remains backward compatible
- imported SWE-bench/Aider/OpenHands/custom benchmark records persist
- benchmark summary calculates trace completion, success, and recommendation rates
- dashboard displays benchmark suite coverage

Non-goals:

- no automatic SWE-bench dataset download
- no full SWE-bench harness execution
- no automatic OpenHands installation
- no claim of official benchmark performance unless `run_mode` is official and externally verified

## 9. v1.0 Optimization Recommendations

Goal:
Move from observability to actionable optimization recommendations.

Features:

- context/prefix caching recommendations
- small-model vs large-model routing recommendations
- tool-wait-aware scheduling recommendations
- retry-loop reduction recommendations
- estimated savings model
- recommendation confidence score

Validation:

- recommendations are backed by trace evidence
- user can identify top 3 cost/time improvements
- at least one controlled demo shows 25-30% estimated or measured improvement

Implemented v1.0 vertical slice:

- `GET /api/tasks/{task_id}/optimizations`
- top recommendation cards in the task dashboard
- evidence/action fields for each recommendation
- estimated time and cost savings
- confidence score
- deterministic rules backed by analysis metrics

Implemented v1.0 validation scaffolding:

- `GET /api/tasks/{task_id}/validation`
- validation metadata on imported tasks
- before/after comparison via `before_after_pair_id`
- repeated input token reduction percent
- estimated cost reduction percent
- latency change percent
- success-preserved check
- dashboard validation section
- documented plan in `docs/V1_VALIDATION_PLAN.md`

Completed real validation:

- Track B real coding-agent integration was run with Aider + OpenAI.
- A real local pytest bugfix workflow was traced: failing test, Aider patch, tests passing afterward, model/token/cost capture, file event, recommendation, and dashboard validation.

Remaining validation items to bring back:

1. Track A: Official SWE-bench Lite/Verified mini-suite
   - Install/download required SWE-bench or dataset tooling.
   - Select a small 1-3 task smoke set first, then expand to 10-25 tasks.
   - For each task, run a real coding agent, capture trace, validate patch/test result, and import trace.
   - Measure trace completion rate, useful bottleneck rate, actionable recommendation rate, task success/failure, cost, latency, retries, and files changed.
   - Do not claim SWE-bench validation until official tasks are actually executed.

2. Track C: Broader real before/after repeated-context optimization experiment
   - Repeat the completed v1.5 controlled OpenAI experiment across more realistic coding tasks.
   - Use a controlled custom agent where prompt/context assembly is under our control.
   - Run each task twice:
     - baseline: repeated stable context sent across model calls
     - optimized: stable context separated, summarized, or removed from repeated calls
   - Capture both traces with the same `before_after_pair_id`.
   - Measure actual repeated input token reduction, estimated cost reduction, latency change, and success preservation.
   - Do not claim real KV-cache control; only claim measured context/prefix reuse opportunity.

Recommended next validation order:

1. Run Track A official SWE-bench smoke set with 1-3 tasks.
2. Expand Track C controlled OpenAI validation to multiple coding tasks.
3. Expand Track A to 10-25 tasks only after the smoke run is stable.

Non-goals:

- no full SWE-bench runner yet
- no real KV-cache control
- no hardware simulation

## 9A. Phase 1.011 Workload Evaluation + Recommendation Package

Goal:
Create the formal Phase 1 exit artifact from existing v0.1-v5.0 evidence.

Product definition:
Phase 1.011 is not v6.0 and not a new runtime layer. It is the package that summarizes what the workload is doing, what the user should do next, what to test in Phase 1.5, and which signals are strong enough to feed Phase 2.

Features:

- Workload Evaluation Package
- Workload Recommendation Package
- metric quality scorecard
- architecture readiness score
- prioritized recommendations
- current infrastructure action plan
- Phase 1.5 Existing Hardware Test Plan
- Phase 2 Architecture Signal Summary
- do-not-do-yet list
- Markdown export

Validation:

- package generation works from local traces/reports
- package persists and can be retrieved
- Markdown export works
- dashboard renders the latest package
- copy does not claim hardware validation unless measured telemetry exists

Non-goals:

- no new SWE-bench/OpenHands execution
- no real vLLM/SGLang/Dynamo integration
- no hardware simulation
- no ASIC/RTL/FPGA/chip artifact
- no architecture bet selection before Phase 1.5

## 10. v3.0 Hardware-Aware Runtime

Goal:
Add backend/hardware-aware signals.

Features:

- GPU/CPU utilization import
- queue time tracking
- backend metadata
- prefill/decode classification
- KV/cache locality hints
- SLO-qualified goodput metrics

Validation:

- dashboard shows task-level + hardware-level bottlenecks
- blueprint recommendations become more evidence-based

## 11. Agent Silicon Blueprint Evolution

v0.1:
Rule-based preview cards.

v1.0:
Trace-derived architecture report.

v2.0:
Memory hierarchy recommendation:

- HBM
- DRAM
- CXL
- NVMe
- object storage

v3.0:
Hardware primitive ranking:

- persistent KV cache
- prefix matching
- context switching
- branch checkpointing
- KV compression/decompression
- prefill/decode split
- DPU/NIC/storage offload

v4.0:
Trace replay simulator.

## 12. What Not To Build Yet

Do not build:

- real chip simulator
- real KV-cache manager inside vLLM/SGLang
- production enterprise auth
- cloud billing
- hardware RTL
- FPGA prototype
- full multi-agent scheduler
- every coding-agent integration

## 13. Release Acceptance Criteria

Each version must include:

- working demo
- tests
- README update
- clear limitations
- sample trace or example
- validation checklist
- no overclaiming

## 14. How Codex Should Use This Document

Codex must treat this file as the source of truth for version scope.

Before starting a new implementation task:

1. Identify target version.
2. Read that version's goal, features, non-goals, and validation.
3. Implement only that version's scope.
4. Run tests.
5. Update README/DEMO/CHANGELOG.
6. Do not jump ahead unless explicitly instructed.

Simple answer:

Right now, the v0.1/v0.2/v0.3 stages are mostly in our conversation and partially scattered across the planning docs.

The document where they should live going forward is:

`docs/VERSION_ROADMAP.md`

That should become Codex's source of truth for the next build stages.



# Agent Runtime Layer + Agent Silicon Blueprint — Post-v1 Version Roadmap

## Product Thesis
Runtime first as the measurement and learning engine. Silicon Blueprint second as the architecture and acceleration engine.

## Strategic Transition
v1.0 recommends. v1.5 executes. v2.0 schedules. v2.5 routes. v3.0 measures hardware. v3.5 designs architecture. v4.0 simulates future hardware. v5.0 becomes the platform.

## Roadmap Table
| Version | Name | Goal | Primary Output |
|---|---|---|---|
| v1.0 | Optimization Recommendations | Repeated-context recommendations and first measurable improvement | Recommendation cards + before/after metrics |
| v1.5 | Optimization Executor | Apply safe repeated-context optimizations automatically | Optimized prompt package + measured savings |
| v2.0 | Runtime Scheduler | Schedule agent steps based on priority/tool wait/SLO | Scheduler decisions + improved idle time |
| v2.5 | Backend-Aware Runtime | Generate routing/cache hints | Prefix-overlap and cache-locality hints |
| v3.0 | Hardware-Aware Runtime | Correlate traces with hardware telemetry | Task-to-hardware bottleneck map |
| v3.5 | Silicon Blueprint Engine | Generate architecture reports from many traces | Memory hierarchy + primitive ranking |
| v4.0 | Trace Replay Simulator | Simulate runtime/hardware improvements | What-if impact projections |
| v4.5 | Replay Validation + Scenario Expansion | Expand scenarios and explain projection credibility | Selectable scenarios + validation evidence |
| v5.0 | Agentic Inference Platform | Combine runtime, blueprint, simulator, benchmarks | Full platform |

## v1.5 Optimization Executor
Goal: automatically apply safe repeated-context optimizations and measure before/after improvement.

Product shift:
v1.0 recommends optimizations. v1.5 generates optimized context packages and before/after savings reports.

Primary endpoint:
`POST /api/tasks/{task_id}/optimize-context`

Features:
- stable context block detection
- dynamic context separation
- context fingerprinting
- prompt package optimizer
- optimized prompt package artifact
- before/after comparison
- measured savings report
- estimated repeated-token reduction
- estimated cost/prefill reduction
- dashboard executor report

Stable context examples:
- system prompt
- tool schemas
- repo summary
- repeated instructions
- repeated context snapshots
- repeated prior observations

Dynamic context examples:
- latest user instruction
- latest tool output
- latest error log
- current test result
- current patch/diff
- current model output

Validation:
- demonstrate 25–30% reduction in repeated input tokens or estimated prefill cost on repeated-context traces
- preserve task success

Non-goals:
- no real KV-cache control yet
- no hardware simulation yet
- no production scheduler yet
- no SWE-bench runner yet
- no backend-aware routing yet

Important wording:
v1.5 produces prefix-cache-ready prompt/context packages. It does not claim real KV-cache hits unless those are measured by a backend integration.

## v2.0 Runtime Scheduler
Goal: schedule agent steps based on priority, tool wait, cost, and task lifecycle.

Features:
- foreground/background priority
- tool-wait-aware scheduling
- retry-loop throttling
- parallelizable step detection
- budget-aware stopping
- SLO-aware scheduling

Validation:
- improve completed tasks/hour or reduce idle time on mixed concurrent agent workloads

Implemented v2.0 vertical slice:

- `POST /api/tasks/{task_id}/schedule`
- `GET /api/tasks/{task_id}/schedule`
- local deterministic scheduler simulation
- persisted scheduler reports
- lifecycle state and task priority
- SLO and budget guard status
- tool-wait scheduling decisions
- orchestration idle-gap scheduling decisions
- retry-throttling scheduling decisions
- dashboard Runtime Scheduler report

Non-goals:

- no production multi-agent scheduler
- no backend-aware routing
- no real KV-cache control
- no hardware simulation

## v2.5 Backend-Aware Runtime
Goal: produce routing and cache hints for inference backends.

Features:
- prefix-overlap estimate
- backend metadata
- queue-depth awareness
- cache-locality hint
- prefill/decode classification
- routing recommendation

Validation:
- show lower TTFT or repeated prefill cost when using prefix-cache-capable backend

Implemented v2.5 vertical slice:

- `POST /api/tasks/{task_id}/backend-hints`
- `GET /api/tasks/{task_id}/backend-hints`
- backend registry
- model-call profiling
- prefix-overlap estimator
- cache-locality classifier
- prefill/decode classifier
- backend-agnostic routing hints
- dashboard Backend-Aware Runtime report

Non-goals:

- no real vLLM integration
- no real SGLang integration
- no real LMCache integration
- no real Dynamo integration
- no production load balancing
- no hardware simulation

## v3.0 Hardware-Aware Runtime
Goal: correlate agent traces with hardware and backend telemetry.

Features:
- GPU/CPU utilization ingest
- queue time tracking
- memory pressure metrics
- prefill/decode timing
- cache hit/miss estimate
- task-level to hardware-level bottleneck map

Validation:
- show at least one trace where agent events explain hardware idle or memory bottleneck

Implemented v3.0 vertical slice:

- imported telemetry schema
- telemetry persistence
- timestamp correlation with model/tool spans
- hardware-aware summary metrics
- task-to-hardware bottleneck map
- dashboard Hardware-Aware Runtime report

Non-goals:

- no live GPU polling
- no full cluster monitoring
- no hardware simulation
- no real vLLM/SGLang/Dynamo metrics scraping yet

## v3.5 Silicon Blueprint Engine
Goal: generate serious architecture reports from many real traces.

Features:
- workload profile
- bottleneck map
- memory hierarchy recommendation
- hardware primitive ranking
- backend/runtime recommendation
- benchmark proposal

Validation:
- generate blueprint report from 100+ real agent traces

## v4.0 Trace Replay Simulator
Goal: simulate runtime/hardware improvements against real traces.

Features:
- persistent KV cache scenario
- prefill/decode split scenario
- tool-wait scheduler scenario
- CXL/warm context tier scenario
- KV compression scenario
- cost/time/watt-dollar projection

Validation:
- replay real traces through 3+ architecture scenarios and compare projected impact

Implemented v4.0 vertical slice:

- `POST /api/blueprints/{blueprint_id}/simulate`
- `GET /api/blueprints/{blueprint_id}/replays`
- `GET /api/replays/{replay_id}`
- persisted trace replay reports
- rule-based scenario projections
- persistent prefix cache scenario
- tool-wait scheduler scenario
- prefill/decode split scenario
- optional warm context tier scenario
- optional KV/context compression scenario
- dashboard Trace Replay Simulator section

Non-goals:

- no real KV-cache control
- no live vLLM/SGLang/LMCache/Dynamo integration
- no production scheduler or router
- no hardware simulation
- no RTL, ASIC design, FPGA output, or watt-dollar measurement

## v4.5 Replay Validation + Scenario Expansion

Goal: make replay projections more configurable, explainable, and validation-ready.

Features:
- selectable replay scenarios
- all five scenario UI support
- replay comparison summary
- projection confidence reason
- real-backend-validation flag
- validation evidence checklist per scenario
- replay Markdown export
- v4.5 validation report

Validation:
- run all five scenarios against a blueprint
- verify replay report includes comparison summary and validation evidence requirements
- verify dashboard renders selectable scenarios and export action
- verify copy does not claim measured backend or hardware speedup

Non-goals:
- no real KV-cache control
- no live backend routing
- no production scheduler
- no hardware simulation
- no measured hardware speedup claims

## v5.0 Agentic Inference Platform
Goal: combine runtime, optimization, hardware-aware telemetry, Silicon Blueprint, and simulation into a full platform.

Features:
- Agent Runtime Layer
- Optimization Executor
- Runtime Scheduler
- Backend-Aware Runtime
- Hardware-Aware Runtime
- Silicon Blueprint Engine
- Trace Replay Simulator
- Benchmark Suite

Validation:
- demonstrate completed agent task improvement across multiple real coding-agent workloads

Implemented v5.0 vertical slice:

- `GET /api/platform/summary`
- `/platform` dashboard
- platform metric cards
- module coverage
- readiness scores
- end-to-end runbook
- measured validation experiment records
- projected-vs-measured token/cost/success comparison
- latest blueprint/replay references
- local-first limitations

Non-goals:

- no cloud SaaS
- no production auth
- no billing
- no real backend control
- no hardware simulation
- no measured improvement claim without benchmark evidence
