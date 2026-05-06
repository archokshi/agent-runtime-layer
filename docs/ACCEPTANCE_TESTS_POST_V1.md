# Post-v1 Acceptance Tests

## v0.5 Benchmark Suite Acceptance Tests

### Backend

- `POST /api/benchmarks/runs` returns 200 for SWE-bench, Aider, OpenHands, and custom benchmark records.
- Benchmark run persistence includes suite name, agent name, run mode, task results, metrics, limitations, and created timestamp.
- `GET /api/benchmarks/runs` returns persisted benchmark runs.
- `GET /api/benchmarks/summary` calculates run count, task count, suite counts, trace completion rate, task success rate, and actionable recommendation rate.
- Platform summary includes benchmark suite coverage.

### Frontend

- Header includes Benchmarks link.
- `/benchmarks` renders benchmark suite metrics and latest runs.
- `/platform` renders benchmark suite coverage.

### Validation

- A smoke SWE-bench/Aider/OpenHands-style record can be imported without executing the external benchmark harness.
- UI/API copy states that imported or smoke records are evidence tracking, not official benchmark scores.
- No copy claims real official SWE-bench or OpenHands validation unless the run was actually executed and marked official.

## Phase 1.011 Acceptance Tests

### Backend

- `POST /api/phase-1-exit/generate` creates a package from existing local evidence.
- Package includes Workload Evaluation Package and Workload Recommendation Package.
- Package includes metric quality scorecard and architecture readiness score.
- Package includes prioritized recommendations.
- Package includes Phase 1.5 Existing Hardware Test Plan.
- Package includes Phase 2 Architecture Signal Summary.
- Package is persisted and listed with `GET /api/phase-1-exit`.
- Package is retrievable with `GET /api/phase-1-exit/{package_id}`.
- Package exports Markdown with `GET /api/phase-1-exit/{package_id}/export.md`.

### Frontend

- Header includes Phase 1 Exit link.
- `/phase-1-exit` renders the latest package.
- Dashboard shows Evaluation Package, Recommendation Package, metric quality scorecard, architecture readiness, Phase 1.5 test plan, Phase 2 signals, and Export Markdown action.

### Validation

- Phase 1.011 uses existing local evidence only.
- UI/API copy says Phase 1.011 is not v6.0, not hardware simulation, and not a new runtime feature layer.
- No copy claims new SWE-bench/OpenHands/vLLM/SGLang/Dynamo/hardware validation was run.

## v1.5 Acceptance Tests

### Backend

- `POST /api/tasks/{task_id}/optimize-context` returns 200 for a repeated-context task.
- Optimizer identifies at least one stable context block.
- Optimizer identifies at least one dynamic context block.
- Optimizer returns baseline and optimized token estimates.
- Optimizer returns repeated-token reduction percentage.
- Optimizer returns estimated cost reduction percentage.
- Optimization report is persisted and retrievable with `GET /api/tasks/{task_id}/optimized-context`.

### Frontend

- Task page shows Run Optimize Context button.
- Optimization Executor Report renders after running optimizer.
- Stable context blocks are visible.
- Dynamic context blocks are visible.
- Baseline vs optimized metrics are visible.
- Savings percentage is visible.
- Optimized prompt package is visible.

### Validation

- Controlled repeated-context sample shows 25-30% reduction in repeated input tokens or estimated prefill cost.
- If validation metadata has `task_success=true`, dashboard shows success preserved.
- No UI or API copy claims real KV-cache control.

## v2.0 Acceptance Tests

### Backend

- `POST /api/tasks/{task_id}/schedule` returns 200 for an imported trace.
- Scheduler report includes lifecycle state, task priority, SLO status, budget status, and scheduler decisions.
- Tool-heavy traces produce a tool-wait scheduling decision.
- Idle-heavy traces produce an idle-gap scheduling decision.
- Retry-loop traces produce a retry-throttling decision.
- Scheduler report is persisted and retrievable with `GET /api/tasks/{task_id}/schedule`.

### Frontend

- Task page shows a Runtime Scheduler section.
- Runtime Scheduler section has a Run Scheduler Tick button.
- Dashboard shows naive vs scheduled estimated duration.
- Dashboard shows idle reduction and simulated tasks/hour.
- Dashboard shows scheduler decisions with rationale, action, confidence, and estimated savings.

### Validation

- Controlled tool-heavy trace shows reduced estimated duration versus naive execution.
- Runtime Scheduler copy clearly says it is a local deterministic simulation.
- No UI or API copy claims production multi-agent scheduling, backend-aware routing, or hardware simulation.

## v2.5 Acceptance Tests

### Backend

- `POST /api/tasks/{task_id}/backend-hints` returns 200 for an imported trace.
- Backend-aware report includes a backend registry.
- Backend-aware report includes model-call profiles.
- Prefix-overlap estimate is calculated from repeated context/cache opportunity.
- Prefill/decode classification is present.
- Cache-locality classification is present.
- Routing hints are generated for repeated-context traces.
- Backend-aware report is persisted and retrievable with `GET /api/tasks/{task_id}/backend-hints`.

### Frontend

- Task page shows a Backend-Aware Runtime section.
- Backend-Aware Runtime section has a Generate Backend Hints button.
- Dashboard shows prefix overlap, cache locality, prefill/decode classification, model-call count, and queue depth.
- Dashboard shows routing hints with rationale, action, target backend, and confidence.
- Dashboard shows model-call profiles.

### Validation

- Controlled repeated-context trace recommends a prefix-cache-capable backend target.
- Controlled queue-depth trace recommends avoiding a saturated backend queue.
- UI and API copy clearly say hints are backend-agnostic.
- No UI or API copy claims real vLLM/SGLang/LMCache/Dynamo integration or production load balancing.

## v3.0 Acceptance Tests

### Backend

- `POST /api/tasks/{task_id}/telemetry/import` imports hardware/backend telemetry samples.
- Telemetry import rejects mismatched task IDs.
- `GET /api/tasks/{task_id}/hardware-analysis` returns a hardware-aware report after telemetry import.
- Report includes telemetry summary metrics.
- Report correlates telemetry samples with model/tool event windows.
- Report classifies queue saturation, memory pressure, cache miss pressure, prefill/decode bottlenecks, and GPU underutilization when evidence exists.

### Frontend

- Task page shows a Hardware-Aware Runtime section.
- Without telemetry, the section tells the user to import telemetry JSON.
- With telemetry, dashboard shows sample count, GPU utilization, memory usage, queue depth, prefill/decode timing, cache hit rate, bottlenecks, and correlated windows.

### Validation

- Sample telemetry fixture produces a task-to-hardware bottleneck map.
- GPU-underutilized sample telemetry fixture produces a GPU-underutilized bottleneck.
- UI and API copy clearly say v3.0 uses imported telemetry only.
- No UI or API copy claims live GPU polling, full cluster monitoring, or hardware simulation.

## v3.5 Acceptance Tests

### Backend

- `POST /api/blueprints/generate` returns a v3.5 Silicon Blueprint report for imported traces.
- Report includes workload profile, bottleneck map, memory hierarchy recommendations, hardware primitive rankings, backend/runtime recommendations, benchmark proposals, and limitations.
- Report includes validation summary with local trace count, 100-trace target progress, telemetry coverage, and remaining validation items.
- Report can be generated from explicit `task_ids` or all local tasks.
- Report is persisted and retrievable with `GET /api/blueprints/{blueprint_id}`.
- Reports are listed with `GET /api/blueprints`.
- Report is exportable as Markdown with `GET /api/blueprints/{blueprint_id}/export.md`.

### Frontend

- Header shows a Blueprints link.
- `/blueprints` page renders the Silicon Blueprint Engine.
- Generate Blueprint button calls the backend and displays the latest report.
- Dashboard shows workload metrics, bottleneck map, memory hierarchy, primitive rankings, backend/runtime recommendations, benchmark proposals, and limitations.
- Dashboard shows validation coverage and Export Markdown action.

### Validation

- Controlled repeated-context and backend-queue traces generate non-empty architecture recommendations.
- Imported telemetry bottlenecks are reflected in the bottleneck map and primitive scores.
- Broader local validation report is documented in `docs/V3_5_VALIDATION_REPORT.md`.
- UI and API copy clearly say this is a rule-based architecture report.
- No UI or API copy claims ASIC design, RTL, FPGA output, hardware simulation, or measured hardware improvement.

## v4.0 Acceptance Tests

### Backend

- `POST /api/blueprints/{blueprint_id}/simulate` returns a v4.0 Trace Replay Simulator report.
- Default replay includes persistent prefix cache, tool-wait scheduler, and prefill/decode split scenarios.
- Scenario results include baseline metrics, projected metrics, reduction percentages, evidence, confidence, and projection-only notes.
- Replay report is persisted and retrievable with `GET /api/replays/{replay_id}`.
- Blueprint replay history is listed with `GET /api/blueprints/{blueprint_id}/replays`.

### Frontend

- `/blueprints` page shows Trace Replay Simulator section.
- Run Replay button calls the simulator endpoint.
- Dashboard shows scenario cards with duration, input token, cost, and prefill reductions.
- Dashboard shows confidence and limitations.

### Validation

- Controlled repeated-context and backend-queue traces produce non-empty replay projections.
- At least three scenarios are replayed for the selected blueprint.
- UI and API copy clearly say projections are not measured backend or hardware speedups.
- No UI or API copy claims real KV-cache control, live backend routing, hardware simulation, RTL, ASIC design, FPGA output, or watt-dollar measurement.

## v4.5 Acceptance Tests

### Backend

- `POST /api/blueprints/{blueprint_id}/simulate` accepts explicit `scenario_ids`.
- All five scenarios can be replayed in one report.
- Replay report includes scenario selection, comparison summary, confidence reason, real-backend-validation flag, and validation evidence checklist.
- `GET /api/replays/{replay_id}/export.md` returns a Markdown replay report.

### Frontend

- `/blueprints` page shows checkboxes for all five scenarios.
- Run Replay uses selected scenarios.
- Replay report shows best duration, best cost, and best prefill scenario summary.
- Replay scenario cards show confidence reason and validation evidence needed.
- Dashboard exposes Export Replay action.

### Validation

- Controlled blueprint can replay all five scenarios.
- Markdown export includes comparison summary and validation evidence.
- UI and API copy clearly say projections are not measured backend or hardware speedups.
- No UI or API copy claims real KV-cache control, live backend routing, hardware simulation, RTL, ASIC design, FPGA output, or watt-dollar measurement.

## v5.0 Acceptance Tests

### Backend

- `GET /api/platform/summary` returns platform version v5.0.
- `POST /api/validation/experiments` stores a measured validation experiment.
- `GET /api/validation/experiments` lists measured validation experiments.
- Summary includes metrics, module coverage, readiness scores, end-to-end runbook, latest blueprint ID, latest replay ID, and limitations.
- Summary includes measured validation experiments when present.
- Readiness covers optimization, backend validation, hardware-aware analysis, Silicon Blueprint, and measured benchmark work.
- Runbook covers trace, analyze, optimize, schedule, backend, telemetry, blueprint, and replay.

### Frontend

- Header includes Platform link.
- `/platform` page renders platform overview.
- Dashboard shows metric cards, runbook, readiness scores, module coverage, and limitations.
- Dashboard shows measured validation records with projected vs measured token/cost results.

### Validation

- Platform summary aggregates existing reports across v0.1-v4.5 features.
- Existing v1.5 real OpenAI before/after result can be stored as a measured validation experiment.
- UI and API copy make clear v5.0 is local-first overview only.
- No UI or API copy claims cloud SaaS, production auth, billing, real backend control, hardware simulation, or measured improvement without benchmark evidence.
