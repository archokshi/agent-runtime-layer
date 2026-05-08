# Canonical Agentium Phase 1 And Phase 2 Roadmap

## Summary

This document is the canonical long-term project roadmap for the YC RFS-aligned Agentium direction.

This document is the source of truth for:

```text
Phase 1 = Agent Runtime Layer
Phase 2 = Agentic Inference System Blueprint Validation
```

The non-negotiable thesis:

> Agents are not prompt-in/response-out inference workloads. They are execution graphs with loops, tool calls, branching, backtracking, persistent context, repeated KV/prefix state, CPU orchestration, I/O waits, and bursty model calls. Agentium's goal is runtime/compiler/backend/hardware co-design for this agent loop.

Phase 1 must only produce evidence Phase 2 consumes. If Phase 2 does not use it, Phase 1 should not build it.

## Extreme Co-Design Lens

Agentium evaluates agentic inference as a full-stack co-design problem across runtime, compiler, serving backend, CPU orchestration, GPU execution, memory hierarchy, KV/cache retention, networking/fabric, and hardware primitives.

No single chip, backend, scheduler, or cache feature should be assumed to solve the full agent loop. Agentium's job is to map measured agent-loop evidence to the right system architecture, then decide whether the product should be software, backend integration, memory fabric/appliance, accelerator/IP, FPGA, ASIC, or partner work.

Agent Silicon Blueprint remains an important Phase 2 artifact, but it is not the whole Phase 2. Phase 2 first produces an agentic inference system blueprint and only narrows toward hardware primitives when system-level evidence justifies that move.

## Phase 1: Agent Runtime Layer

Purpose:

Measure agentic inference workloads and generate trusted evidence for the Phase 2 Agentic Inference System Blueprint.

Current status:

Phase 1.0 Developer Preview is released.

Phase 1 sub-phases:

- **Phase 1.0 Developer Preview**
  Current open-source profiler, dashboard, SDK, CLI, examples, optimizer, workload report.

- **Phase 1.1 Real Trace Corpus Expansion**
  Capture 100+ real coding-agent traces. Phase 2 consumes execution graph shapes, tool/model/CPU/I/O split, retry/backtrack frequency, context lifetime, and outcome distribution.
  Implementation hook: `GET /api/corpus/summary` and `/corpus` generate a Trace Corpus Manager report that shows corpus volume, event coverage, outcome metadata, Phase 2 evidence readiness, missing evidence, and no-overclaiming boundaries.

- **Phase 1.2 Benchmark And Validation Corpus**
  Capture SWE-bench/Aider/OpenHands/custom benchmark-style traces. Phase 2 consumes realistic repeatable workloads, success/failure outcomes, before/after optimization pairs, and repeated-context experiments.
  Implementation hook: `GET /api/benchmarks/validation` and `/benchmarks` show benchmark validation readiness, suite coverage, run-mode truth labels, outcome coverage, trace completion, and before/after optimization pairs.

- **Phase 1.3 Backend And Telemetry Evidence Capture**
  Import backend/hardware telemetry. Phase 2 consumes GPU utilization, CPU orchestration utilization, queue depth, memory pressure, TTFT/ITL, prefill/decode timing, and cache hit/miss data.
  Implementation hook: `GET /api/telemetry/summary` and `/telemetry` show imported telemetry readiness, measured field coverage, backend symptom counts, and Phase 2 evidence value for backend/hardware gap analysis.

- **Phase 1.4 Evidence Quality And Metric Confidence**
  Label every metric as measured, estimated, inferred, or missing. Phase 2 consumes confidence scores, metric source labels, missing evidence lists, and no-overclaiming boundaries.
  Implementation hook: `GET /api/evidence/quality` and `/evidence` provide metric confidence labels, missing evidence, Phase 2 safety rules, and no-overclaiming boundaries across trace, optimization, benchmark, and telemetry evidence.

- **Phase 1.5 Phase 2 Handoff Package**
  Package Phase 1 evidence into a stable Phase 2 input dataset. Phase 2 consumes corpus summary, metric inventory, architecture signal seeds, missing measurement checklist, and do-not-claim list.
  Implementation hook: `POST /api/phase-2-handoff/generate`, `GET /api/phase-2-handoff`, Markdown export, and `/phase-2-handoff` package Phase 1.1 through Phase 1.4 evidence into Phase 2.0 through Phase 2.4 input sections.

- **Phase 1.6 Evidence Campaign**
  Run the evidence collection campaign needed to fill the Phase 1.5 handoff package with enough real data for Phase 2. Phase 2 consumes the resulting trace corpus, benchmark-linked validation runs, before/after optimization pairs, backend telemetry imports, evidence quality scores, and regenerated handoff package.

  Phase 1.6 is not a new dashboard feature layer. It is the operational campaign that uses Phase 1.1 through Phase 1.5 to produce credible Phase 2 input.

  Purpose:

  Turn Agent Runtime Layer from a working profiler into a credible workload evidence engine for Agentic Inference System Blueprint Validation.

  Core question:

  ```text
  What should agentic inference runtime/backend/system/hardware architecture optimize for?
  ```

  Primary outputs:

  - real trace corpus
  - benchmark validation corpus
  - before/after optimization pairs
  - validation metadata
  - regenerated evidence quality report
  - regenerated Phase 2 handoff package
  - Phase 2 test plan updates

  Minimum campaign target:

  - 25+ real coding-agent traces with model/tool/file/terminal/context events
  - 10+ benchmark-style traces with task outcomes and trace completion
  - 5+ baseline/optimized pairs for repeated-context and tool-wait experiments
  - backend telemetry imports where available: GPU utilization, CPU utilization, queue depth, memory pressure, TTFT/ITL, prefill/decode timing, cache hit/miss metrics, and fabric/network symptoms where available
  - regenerated Phase 2 handoff package after the campaign
  - updated evidence quality report showing what is measured, estimated, inferred, and missing

  Every useful Phase 1.6 trace should capture:

  - `task_start`
  - `task_end`
  - model call events
  - tool call events
  - file events
  - terminal/test events
  - context snapshots
  - token counts
  - cost estimate
  - retry/backtrack evidence where possible
  - success/failure outcome
  - files changed count
  - tests passed/failed when available

  Campaign tracks:

  - **Track A: Real Coding-Agent Runs**
    Capture Aider, SDK custom-agent, local CLI-wrapped, native coding-agent, and repo edit/test/retry workflows. Phase 2 consumes model/tool split, repeated context, tool wait, retries, execution graph shape, context lifetime, and cost/time/token profile.

    - **Phase 1.6A: Codex Native Capture**
      Uses Codex hooks first to capture prompt, session, tool, file, terminal, and stop events. Repo-local hooks are supported, and global Codex hook install is the preferred live-validation path when project-local trust blocks hook loading. Source-checkout global installs must use a Python module launcher so live validation does not require `agent-runtime` to already be installed globally. The installer should enable the current `hooks` feature flag; older `codex_hooks` references are deprecated in current Codex CLI builds. Future extension: Codex App Server stream. Phase 2 consumes Codex execution graph structure, tool/file/terminal evidence, prompt-to-tool cadence, context lifetime signals, and retry/tool-wait patterns.
      If a specific Codex CLI mode or platform does not fire hooks reliably, use the implemented Codex session JSONL importer as the post-run fallback capture path. `codex exec --json` stream support remains a future fallback extension if the CLI exposes a stable event stream for the same data.

    - **Phase 1.6B: Claude Code Native Capture**
      Uses Claude Code hooks to capture prompt, session, tool success/failure, file, terminal, stop, and session-end events. Phase 2 consumes Claude Code execution graph structure, tool success/failure timing, file/terminal evidence, context lifetime signals, and retry/tool-wait patterns.

    - **Phase 1.6C: Cursor Agent Capture**
      Uses Cursor Agent CLI `stream-json` first to capture system, user, assistant, tool-call start/end, and result events. Future extension: Cursor Background Agents API import. Phase 2 consumes Cursor agent execution structure, tool/file evidence, result timing, and workflow outcome signals.

  - **Track B: Benchmark-Style Runs**
    Capture SWE-bench-style, Aider-style, controlled bug-fix, and failing-test-to-passing-test tasks. Phase 2 consumes representative workload slices, task success/failure, tests passed/failed, patch generation, trace completion, cost/task, and latency/task.

  - **Track C: Before/After Optimization Pairs**
    Capture baseline vs optimized versions of repeated-context and tool-wait tasks. Phase 2 consumes input-token reduction, repeated-token reduction, estimated cost reduction, latency change, success preservation, and architecture signals for persistent context, prefix reuse, and cache-aware backend tests.

  - **Track D: Telemetry Imports, If Available**
    Import GPU utilization, CPU utilization, memory pressure, queue depth, TTFT, ITL, prefill timing, decode timing, and KV/cache hit rate when available. Phase 1 owns import/reporting. Phase 2 owns real backend/hardware experiments and interpretation.

  Phase 1.6 success criteria:

  - Phase 2.0 can build an agentic inference workload model from real traces.
  - Phase 2.1 has a concrete backend/system test plan or measured backend telemetry.
  - Phase 2.2 has candidate runtime-system-hardware interface signals grounded in trace fields.
  - Phase 2.3 has repeated-context and memory/cache evidence separated from real KV-cache claims.
  - Phase 2.4 has execution graph and retry/tool-wait evidence for compiler/runtime modeling.
  - Phase 1.6 can support a system bottleneck map across model, tool, CPU, I/O, context/KV, cache, queueing, memory, backend telemetry, and fabric/network symptoms where available.
  - Phase 1.5 handoff score improves materially, or clearly explains which evidence is still missing.

  Phase 1.6A/B/C shared acceptance criteria:

  - installed integration can capture at least one real run
  - trace appears in the dashboard
  - trace includes task start/end, prompt/session metadata, and tool/file/terminal evidence where available
  - Phase 1.6 Evidence Campaign counts the trace as coding-agent evidence
  - Phase 2 handoff can consume the trace evidence

  Minimum exit criteria:

  - 25+ real coding-agent traces
  - 10+ benchmark-style traces
  - 5+ before/after optimization pairs
  - all useful traces include outcome metadata
  - evidence quality report regenerated
  - Phase 2 handoff regenerated
  - missing backend/system/hardware evidence clearly listed

  Strong exit criteria:

  - 100+ real coding-agent traces
  - 25+ benchmark-style traces
  - 10+ before/after optimization pairs
  - telemetry from at least one real backend
  - repeated context, tool wait, retry, or queue/cache-locality patterns recur across the corpus
  - Phase 2 handoff score materially improves and explains remaining evidence gaps

  Phase 1.6 must not:

  - add unrelated product features
  - claim official benchmark results from local smoke runs
  - claim real KV-cache hits without backend cache telemetry
  - claim hardware speedup without real backend/hardware measurement
  - claim internal model telemetry unless exposed by the coding agent, provider, or backend telemetry
  - build production SaaS monitoring
  - start Phase 2 architecture decisions before regenerating the handoff package

  Exit artifact:

  ```text
  Phase 1.6 Evidence Campaign Report
  +
  Updated Phase 2 Handoff Package
  +
  Clear Phase 2 test plan
  ```

Phase 1 must not build:

- SaaS/team features
- billing/auth/user management
- generic LLMOps dashboards
- prompt playgrounds
- random integrations not needed by Phase 2
- production scheduler
- real KV-cache manager
- hardware simulation
- RTL/FPGA/ASIC/chip design

## Phase 2: Agentic Inference System Blueprint Validation

Purpose:

Convert Phase 1 evidence into a validated runtime/compiler/backend/system/hardware architecture direction for agentic inference.

Phase 2 begins with system blueprint generation and then validates the blueprint through existing-backend/system evaluation, prototype measurements, trace replay simulation, and hardware primitive feasibility work.

Phase 2 final output:

```text
Agentic Inference System Blueprint Validation Package
```

The final package must include:

- agentic workload model
- system bottleneck map
- existing backend/system fit report
- runtime-system-hardware interface
- memory/KV/context architecture
- agentic compiler model
- Agent Silicon Blueprint hardware section
- architecture decision memo
- backend/context-memory prototype report
- real system/platform benchmark report
- trace replay system simulation report
- hardware primitive microarchitecture spec, only if justified
- RTL/FPGA feasibility spike report, only if justified
- go/no-go recommendation for software, backend integration, memory fabric/appliance, accelerator/IP, FPGA, ASIC, or partner work

Phase 2 sub-phases:

- **Phase 2.0 Agentic Inference Workload Model**
  Define the agent loop as a system workload: execution graph, model/tool/I/O/CPU phases, branch/retry structure, context/KV lifetime, tool/I/O gaps, CPU orchestration, KV reuse distance, prefill/decode pressure, cache locality, and utilization-collapse hypotheses.

- **Phase 2.1 Existing Backend/System Gap Analysis**
  Evaluate how far existing backend and system stacks go: GPU baseline, vLLM-style prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, Dynamo-style routing, CPU orchestration, GPU utilization, queueing, batching, memory pressure, cache hit/miss behavior, and networking/fabric implications where available.

  Phase 2.1 has two levels:

  - **Phase 2.1A Gap Analysis Framework**
    Analyze workload artifacts and imported telemetry. Produce backend/system gap findings or a test plan when telemetry is missing.

  - **Phase 2.1B-G Real Existing Backend/System Evaluation**
    Run or import real measurements for baseline GPU/CPU/backend behavior, vLLM-style prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, Dynamo-style cache-aware routing studies, queueing/batching, memory pressure, and fabric/network symptoms where available. Produce an Existing Backend/System Fit Report.

- **Phase 2.2 Runtime-System-Hardware Interface**
  Define hints/contracts the runtime must expose to backend, system, and hardware layers: execution graph ID, dependency graph, stable prefix ID, context block fingerprint, KV reuse distance, branch checkpoint ID, retry boundary, SLO/priority, prefill/decode class, cache retention hint, routing locality hint, queue/scheduler hint, and memory tier hint.

- **Phase 2.3 Memory/KV/Context Architecture**
  Define persistent context architecture: context working set, cache TTL, HBM/DRAM/CXL/NVMe/object storage placement, persistent KV/context storage, prefix matching, warm context tier, shared context accessibility, branch checkpointing, KV compression/decompression, and retention/eviction policy.

- **Phase 2.4 Agentic Compiler / Execution Graph Model**
  Define the compiler/runtime layer that coordinates the whole system: execution graph IR, static vs dynamic scheduling, cache/prefix planning, branch checkpoint planning, prefill/decode placement, memory-tier placement, tool-wait overlap, backend placement, and routing/cache locality decisions.

- **Phase 2.5 Agentic Inference System Blueprint v1**
  Produce the formal system blueprint: workload requirements, system bottleneck map, existing-platform gaps, runtime-system-hardware interface, memory/KV/context architecture, compiler model, Agent Silicon Blueprint hardware section, primitive ranking, architecture bet candidates, evidence confidence score, and do-not-build-yet list.

- **Phase 2.6 Architecture Bet Decision**
  Select the first concrete system architecture bet to validate. Candidate bets include Agent Context Memory Fabric, prefill/decode-aware serving path, graph-aware runtime scheduler, branch checkpoint runtime, or a narrower hardware primitive if system evidence justifies it. Output an Architecture Decision Memo with evidence, risks, alternatives, and go/no-go criteria.

  Phase 2.6 contains the architecture bet candidates as sub-tracks:

  - **Phase 2.6A Agent Context Memory Fabric**
    Lead system architecture bet. Priority P0. Focus: preserving, routing, and reusing agent context/KV state across execution graphs. It coordinates runtime hints, backend cache behavior, stable prefix reuse, reuse-distance-aware retention, HBM/DRAM/CXL/NVMe-style memory tiering, prefill/decode pressure, and possible future fabric/hardware primitives. This is the first bet to prototype in Phase 2.7 unless stronger evidence changes the decision.

  - **Phase 2.6B Prefill/Decode-Aware Serving Path**
    Supporting bet. Priority P1. Focus: separating or scheduling prefill-heavy and decode-heavy agent model calls differently. This supports the memory fabric because repeated context often appears as prefill pressure.

  - **Phase 2.6C Graph-Aware Runtime Scheduler**
    Supporting bet. Priority P1. Focus: using the agent execution graph, dependency graph, SLO/priority, queue state, and cache locality hints to schedule or route model calls. This supports the memory fabric by helping route future calls toward retained context.

  - **Phase 2.6D Branch Checkpoint Runtime**
    Deferred bet. Priority P2. Focus: preserving branch/retry state to reduce recomputation during backtracking. This needs a larger retry/backtrack corpus before becoming the lead bet.

  Phase 2.6 decision rule:

  ```text
  Select one lead bet, list supporting mechanisms, and defer bets that lack enough evidence.
  ```

- **Phase 2.7 Agent Context Memory Fabric Backend Prototype**
  Prototype the selected Phase 2.6 lead bet first, expected default: Phase 2.6A Agent Context Memory Fabric. Integrate or evaluate context/KV reuse behavior inside existing backend infrastructure such as vLLM prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, or Dynamo-style cache-aware routing. Measure real cache hit/miss, TTFT, prefill time, task latency, and task success. This is the first point where Agentium may claim measured backend KV/cache behavior, only for the backend tested.

- **Phase 2.8 Real System/Platform Benchmark**
  Run baseline vs optimized workloads on real system/platform stacks. Compare baseline GPU serving, cache-aware backend behavior, CPU orchestration impact, memory pressure, queueing/routing, and optional fabric/network implications where available. Measure task latency, GPU/CPU utilization, memory pressure, queue depth, TTFT, ITL, prefill/decode timing, cache hit/miss, cost/task where available, and task success preservation. This is the first point where Agentium may claim measured system/hardware improvement, only for the tested workload and platform.

- **Phase 2.9 Trace Replay System Simulator**
  Build a trace replay simulator for candidate system architectures. Model baseline GPU serving, GPU plus prefix cache, persistent context memory tiers, CPU orchestration improvements, prefill/decode disaggregation, HBM/DRAM/CXL/NVMe/object storage tiers, cache capacity, cache hit/miss assumptions, and sensitivity analysis. This supports system/hardware simulation claims but still does not prove real hardware speedup.

- **Phase 2.10 Hardware Primitive Microarchitecture Spec**
  Specify the strongest validated primitive only after system/platform evidence shows a specific unsolved gap worth hardware attention. Candidate primitives include a persistent KV/cache controller, context fingerprint matcher, branch checkpoint buffer, prefill/decode scheduler, memory-tier controller, or fabric/offload interface. Include data path, control path, interfaces, expected metrics, and validation plan.

- **Phase 2.11 RTL/FPGA Feasibility Spike**
  Optionally explore feasibility for one primitive only if Phase 2.7-2.10 justify it. Output may include a small RTL sketch, testbench, synthesis/FPGA feasibility notes, or partner evaluation. This is not complete chip design and must not claim production silicon readiness.

Claim ladder:

- After **Phase 2.5**: evidence-backed agentic inference system blueprint.
- After **Phase 2.7**: measured backend KV/cache behavior, if validated on a real backend.
- After **Phase 2.8**: measured system/hardware improvement, if validated on a real system/platform.
- After **Phase 2.9**: trace replay simulation for candidate system/runtime/hardware architectures.
- After **Phase 2.10**: concrete hardware primitive specification.
- After **Phase 2.11**: RTL/FPGA feasibility direction, not production chip design.

Phase 2 must not:

- claim real system/hardware speedup without Phase 2.8 real system/platform measurement
- claim real KV-cache control without Phase 2.7 backend integration or measured backend cache telemetry
- claim hardware simulation before Phase 2.9 trace replay simulator exists
- claim RTL/FPGA feasibility before Phase 2.11 feasibility work exists
- claim ASIC/chip readiness during Phase 2
- claim a single chip solves the agentic inference problem unless system-level CPU/GPU/memory/network/runtime evidence supports it
- skip existing backend evaluation
- jump directly to RTL/FPGA/ASIC
- become generic observability
- invent evidence Phase 1 did not produce

## Collaboration Contract

Phase 1 owns:

- trace capture
- SDK/CLI/adapters
- benchmark records
- telemetry import
- analyzer metrics
- workload reports
- validation metadata
- evidence confidence labels

Phase 2 owns:

- workload-to-architecture interpretation
- backend/system/hardware gap analysis
- runtime-system-hardware interface
- memory/KV/context architecture
- agentic compiler model
- primitive ranking
- blueprint validation
- backend KV/cache prototype evaluation
- real system/platform benchmark interpretation
- trace replay simulation
- hardware primitive specification
- RTL/FPGA feasibility direction, if justified

Decision rule:

```text
A Phase 1 feature is allowed only if it feeds one of Phase 2.0 through Phase 2.11.
```

## Test Plan

Documentation validation:

- `docs/AGENTIUM_PHASE_ROADMAP.md` exists.
- It states the YC RFS thesis as the north star.
- It defines Phase 1 as Agent Runtime Layer.
- It defines Phase 2 as Agentic Inference System Blueprint Validation.
- It contains the Extreme Co-Design Lens.
- It says Phase 1.x work is only allowed if Phase 2 consumes it.
- It moves old hardware evaluation into Phase 2.
- It defines Phase 1.5 as Phase 2 Handoff Package.
- It defines Phase 1.6 as the Evidence Campaign.
- It defines Phase 2.6 through Phase 2.11 as validation/prototype/simulation/feasibility work.
- It contains a claim ladder for real KV-cache behavior, real system/hardware improvement, simulation, and RTL/FPGA feasibility.
- It contains explicit no-overclaiming rules.

Release consistency:

- `docs/VERSION_ROADMAP.md` points to the new phase roadmap for Agentium-level direction.
- `README.md` references the phase roadmap without distracting from the public developer-preview positioning.
- No docs claim real system/hardware speedups, real KV-cache control, RTL, FPGA, ASIC, or hardware simulation before the corresponding Phase 2 validation sub-phase exists.

## Assumptions

- Phase 1.0 is already complete and public as Agent Runtime Layer Developer Preview.
- Phase 1.1 through Phase 1.5 provide the evidence collection, scoring, and handoff mechanisms.
- Phase 1.6 is the evidence campaign that runs those mechanisms enough times to make Phase 2 useful.
- Phase 2 is the next strategic direction after Phase 1.6 produces or clearly gates the required evidence, and now includes system blueprint generation plus blueprint validation.
- Phase 2 must consume measured Phase 1 evidence and must not invent evidence.
- The YC RFS framing is fixed and non-negotiable.
- This document becomes the durable project memory; future work should be checked against it before implementation.
