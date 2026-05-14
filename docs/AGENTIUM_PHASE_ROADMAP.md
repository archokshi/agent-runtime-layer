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

Phase 1 product arc:

```
Phase 1.0–1.6  →  "See it."      Profiler + traces + dashboard + evidence campaign
Phase 1.7      →  "Fix it."      One-click context optimization + proof card
Phase 1.8      →  "Control it."  Budget + retry enforcement via hook infrastructure
Phase 1.9      →  "Remember it." Persistent context memory — compounding savings
Phase 1.10     →  "Own it."      Unified control plane — toggle UI + pricing gates
```

Each phase is a standalone value add. Each unlocks a pricing tier. Observing is always free.
Acting (optimizing, governing, remembering) is paid.

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
  Implementation hook: `POST /api/phase-2-handoff/generate`, `GET /api/phase-2-handoff`, Markdown export, and `/phase-2-handoff` package Phase 1.1 through Phase 1.4 evidence into Phase 2.0 through Phase 2.5 input sections.

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
  - Phase 2.1 has enough workload evidence to produce a spec-based existing platform fit evaluation.
  - Phase 2.2 has a concrete backend/system test plan or measured backend telemetry.
  - Phase 2.3 has candidate runtime-system-hardware interface signals grounded in trace fields.
  - Phase 2.4 has repeated-context and memory/cache evidence separated from real KV-cache claims.
  - Phase 2.5 has execution graph and retry/tool-wait evidence for compiler/runtime modeling.
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

  Backlog:

  - **Phase 1.6 Strong Real-World Evidence Expansion**
    Optional/future expansion after the minimum Phase 1.6 gate. Capture 100+ real external coding-agent traces, 25+ externally repeatable benchmark traces, 10+ before/after pairs, real backend telemetry from vLLM/SGLang/LMCache/Dynamo-style systems where available, official benchmark records where externally executed, and real hardware measurements. This strengthens Phase 2 claims but does not block Phase 2.0 kickoff.

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

- **Phase 1.7 Context Optimizer Runtime**
  Convert the Context Optimizer from an analysis tool into a runtime action. Phase 1.6
  shows developers what to fix. Phase 1.7 lets them fix it in one click and see measured
  proof that it worked. This is the first monetizable product feature.

  Purpose:

  The gap between seeing a problem and fixing it must be one action. Phase 1.7 closes
  that gap. The developer clicks Apply — Agentium strips stable context, runs the
  optimized prompt, captures the before/after delta, and produces a shareable proof card.

  What it builds:

  - `POST /api/tasks/{task_id}/apply-optimization` backend endpoint that runs the
    optimizer and stores an OptimizationProofRecord with before/after token and cost delta
  - `GET /api/optimization-proof/{proof_id}` to retrieve proof records
  - `auto_optimize` flag on `AgentRuntimeTracer` — when True, automatically strips
    stable context blocks before each model call using the optimizer
  - Before/after proof card in the customer dashboard run detail page showing measured
    token reduction, cost reduction, and success preservation
  - Apply Optimization button on run detail page (customer dashboard port 4000)
  - ⚡ Context Optimizer toggle in the Phase 1.10 Control Plane UI — primary delivery
    mechanism; CLI flag `auto_optimize=True` remains as developer fallback
  - /runs page shows ⚡ Fix it badge on any run with ≥20% repeated context tokens

  What the developer gets:

  - One click from "you are wasting 43% of tokens" to "here is the proof it is fixed"
  - Shareable proof card: −44% tokens · −43% cost · success preserved ✓ [measured]
  - SDK flag for zero-friction automation: `auto_optimize=True`
  - Toggle in Control Plane: flip ON → every subsequent run auto-optimized
  - "Gains since enabled" delta card on overview showing cumulative savings

  Evidence quality rule:

  - Labels show `~ Estimated` until a real before/after pair is measured
  - Labels upgrade to `✓ Verified` automatically after a measured pair is stored

  Exit artifact:

  ```text
  At least one OptimizationProofRecord stored in the database
  Before/after proof card visible in the customer dashboard
  auto_optimize flag tested on at least one real agent run
  ```

- **Phase 1.8 Budget Governor**
  Give developers hard controls over agent cost and retry behavior using the existing
  hook infrastructure. PreToolUse hooks can block execution — Phase 1.8 uses this to
  enforce per-project budget caps and retry limits before runaway costs occur.

  Purpose:

  No more $0.124 disaster runs. No more silent retry spirals. The developer configures
  the rules once. Agentium enforces them on every run automatically via hooks that
  already fire before every tool call.

  What it builds:

  - `.agentium/config.yaml` per-repo config file schema supporting:
    `max_cost_per_run`, `max_retries_per_task`, `alert_threshold`, `token_limit_per_call`
  - `packages/sdk-python/agent_runtime_layer/budget.py` — session cost and retry state
    tracker (reads config or API settings, accumulates cost, counts retries per session)
  - Budget enforcement in `claude_code.py` and `codex.py` hook handlers:
    PreToolUse checks budget state → returns blocked result if limit exceeded
  - `GET /api/budget/config` and `POST /api/budget/config` backend endpoints
  - Budget Governor card on customer dashboard overview: actual retry count + estimated
    wasted dollars from existing run data (value-first, not CLI-first empty state)
  - 🛡 Budget Governor toggle in the Phase 1.10 Control Plane UI with inline inputs:
    max cost/run field + max retries field — primary delivery mechanism
  - SDK reads enforcement config from `/api/settings` on startup (not local YAML)

  What the developer gets:

  - "Stopped at retry 3 → saved $0.048" visible in dashboard
  - "Budget cap hit at $0.05 → run terminated" with cost preserved
  - Monthly savings summary from enforced limits across all runs
  - Toggle in Control Plane: flip ON + set limits → enforced from next run forward
  - No YAML editing, no CLI init command required

  Exit artifact:

  ```text
  At least one real run stopped by budget cap (measured, in dashboard)
  At least one real run stopped by retry limit (measured, in dashboard)
  .agentium/config.yaml documented and tested on Codex and Claude Code hooks
  ```

- **Phase 1.9 Agent Context Fabric**
  Persist stable agent context across sessions using a local context memory store and
  a lightweight API proxy. Agentium learns which context blocks are stable across runs
  and automatically adds Anthropic cache_control markers so the developer pays
  $0.30/MTok instead of $3.00/MTok on repeated prefixes. One environment variable
  change. Zero agent code changes.

  Purpose:

  Every cold-start agent run re-sends the same system prompt, tool definitions, and
  repo summary at full price. Phase 1.9 makes that cost disappear. The more runs
  Agentium captures, the more context blocks it recognizes, and the more it saves.
  The developer's trace history becomes their switching cost.

  What it builds:

  - `context_memory` table in the existing SQLite database:
    fingerprint (sha256), content_type, token_count, source_repo, agent_type,
    first_seen_at, last_seen_at, hit_count
  - `packages/sdk-python/agent_runtime_layer/proxy.py` — local API proxy on port 8100:
    intercepts `POST /v1/messages`, extracts stable prefix fingerprints, checks
    context_memory, injects `cache_control: {"type": "ephemeral"}` on matched blocks,
    forwards to real Anthropic API, records cache_read_input_tokens from response
  - `agent-runtime proxy` CLI subcommand to start the proxy (developer fallback)
  - `GET /api/context-memory/summary` backend endpoint showing hit counts and savings
  - Context Memory card on customer dashboard overview: estimated $/run caching
    opportunity shown using existing repeated-context data (value-first empty state)
  - 🧠 Context Memory toggle in Phase 1.10 Control Plane UI — primary delivery;
    enabling toggle starts proxy automatically, sets ANTHROPIC_BASE_URL internally
  - Context Memory section on customer dashboard context page

  What the developer gets:

  - One toggle in the Control Plane — no env var change, no CLI command required
  - Stable context cached at $0.30/MTok instead of $3.00/MTok (90% cost reduction)
  - Savings grow every run — compounding value, increasing switching cost
  - "24,100 tokens from context memory → saved $0.072 this call" in dashboard
  - Context memory is local and private — no data leaves their environment

  Exit artifact:

  ```text
  context_memory table populated from at least one real trace
  Proxy intercepts at least one real agent run with cache_control injection
  Dashboard shows verified cache_read_input_tokens > 0 from Anthropic API response
  Cumulative savings visible in dashboard context memory card
  ```

- **Phase 1.10 Control Plane**
  Unify Phase 1.7, 1.8, and 1.9 under a single toggle-based UI so any developer —
  not just CLI-comfortable ones — can activate all three optimizations in one screen
  and see their gains from the next run forward.

  Problem it solves:

  Phase 1.7–1.9 are built but require CLI commands, YAML config files, and manual env
  var exports. No competitor has a toggle-based control plane for agent cost optimization.
  This is the UX gap Agentium can own.

  User flow:

  ```
  Step 1 — First run (Phase 1.6, already works)
    Developer installs SDK + hooks → runs agent → dashboard shows:
    "65% repeated tokens · $0.0142/run · 3 retries"
    User thinks: "how do I fix this?"

  Step 2 — Control Plane (/settings page)
    User opens localhost:4000/settings
    Sees 3 toggle cards — each showing their OWN data as the value prop:

    ⚡ Context Optimizer    [toggle OFF → flip ON]
       "Your runs waste 65% repeated tokens → ~$0.018 saving/run available"

    🛡 Budget Governor     [toggle OFF → flip ON]
       "3 retries this week → ~$0.009 wasted"
       Max cost/run: [0.10]   Max retries: [3]

    🧠 Context Memory      [toggle OFF → flip ON]
       "65% tokens re-sent every call → ~$0.018/run cacheable"

    User flips toggles → Save → "Active from your next run"

  Step 3 — Next run (the payoff)
    SDK reads /api/settings on startup
    → optimizer ON  → strips repeated context automatically
    → budget ON     → enforces cap + retry limit via hooks
    → memory ON     → proxy injects cache_control markers
    Run completes

  Step 4 — Gains card ("the wow moment")
    Overview page shows new section:
    ┌──────────────────────────────────────────────────┐
    │  Since you turned on optimizations (yesterday)   │
    │  Tokens      48,200 → 27,400    −43%  ✓         │
    │  Cost/run    $0.0142 → $0.0081  −43%  ✓         │
    │  Retries     3 → 0              −100% ✓         │
    └──────────────────────────────────────────────────┘
  ```

  What it builds:

  - `settings` table in SQLite: `optimizer_enabled`, `budget_enabled`, `memory_enabled`,
    `max_cost_per_run`, `max_retries`, `plan`, `enabled_at`,
    `baseline_avg_tokens`, `baseline_avg_cost`, `baseline_retry_count`
    (baseline snapshot captured from last 10 runs when toggle first turns ON)
  - `GET /api/settings` and `PATCH /api/settings` backend endpoints
  - Plan gate enforcement in PATCH: `PLAN_GATES` dict maps feature → allowed plans;
    returns 403 with upgrade message if plan does not have access
  - SDK `_load_remote_settings()` called on `AgentRuntimeTracer.__init__`:
    reads `/api/settings`, applies optimizer/budget/memory config automatically;
    silent fallback to local defaults if API unreachable
  - `/settings` page in customer dashboard: three toggle cards with live value
    estimates computed from user's own run data; budget inputs shown inline when
    budget toggle is ON; PATCH on save; "Active from next run" confirmation banner
  - Pricing gate UI: free-plan toggles render grayed with lock icon and upgrade CTA;
    clicking locked toggle opens upgrade modal showing ROI calculation
  - "Gains since enabled" delta card on `/overview`: compares runs after `enabled_at`
    vs baseline snapshot; shows token delta, cost delta, retry delta; badge ✓ Verified
    when real before/after pairs exist

  Competitive positioning:

  No competitor (Langfuse, Helicone, Portkey, LangSmith, Braintrust, Arize, W&B Weave)
  offers a toggle-based control plane where flipping a switch applies an optimization
  to the developer's next run and shows measured before/after gains. Portkey has budget
  guardrails but requires JSON/YAML config. Helicone has caching but it is always-on
  with no per-feature control. Agentium Phase 1.10 owns this gap.

  Exit artifact:

  ```text
  /settings page live with 3 toggles + plan gates
  PATCH /api/settings enforces plan tier
  SDK reads settings from API on startup
  "Gains since enabled" card visible on overview after first post-enable run
  At least one alpha user activated all 3 toggles and saw gains card
  ```

Phase 1.7 through Phase 1.10 may build:

- Context optimizer runtime (apply, not just recommend)
- Budget and retry control using existing hook infrastructure
- Anthropic prefix cache_control injection (product feature, not custom KV-cache)
- Local API proxy for context interception (self-hosted, no cloud dependency)
- Per-repo configuration files for budget and retry policy (developer fallback)
- Toggle-based control plane UI (primary delivery mechanism for 1.7–1.9)
- Pricing gate enforcement in backend (plan field, PLAN_GATES, 403 on upgrade required)
- "Gains since enabled" delta card using baseline snapshot vs post-enable runs
- SDK reading settings from API on startup (replaces local YAML as primary config)

Phase 1 must not build:

- SaaS/team features
- billing/auth/user management
- generic LLMOps dashboards
- prompt playgrounds
- random integrations not needed by Phase 1.7 through Phase 1.9
- production scheduler
- custom KV-cache implementation (use Anthropic prefix caching instead)
- hardware simulation
- RTL/FPGA/ASIC/chip design

## Monetization Strategy

### Core principle

```
Free  =  You can SEE the problem (observe)
Paid  =  Agentium FIXES it for you (act)
```

Every toggle in the control plane is a pricing gate. Observing is free forever.
Acting — optimizing, governing, remembering — is paid. No per-trace tax, no per-span
billing. Charge for value delivered, not data ingested.

### Pricing tiers

```
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE  — Free ($0)                                           │
├─────────────────────────────────────────────────────────────────┤
│  Unlimited traces + full dashboard (Phase 1.0–1.6)             │
│  "You are wasting 65% tokens" — the insight shown              │
│  "3 retries → ~$0.009 wasted" — the warning shown              │
│  "~$0.018/run cacheable" — the opportunity shown               │
│  ⚡ 🛡 🧠 Toggles visible but locked (lock icon + upgrade CTA) │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PRO  — $49/month (Optimize tier)   [Phase 1.7 unlock]         │
├─────────────────────────────────────────────────────────────────┤
│  ⚡ Context Optimizer toggle — ON                               │
│  Auto-strips repeated context on every run                     │
│  Proof card per run: −44% tokens · −43% cost · ✓ Verified      │
│  "Gains since enabled" delta card on overview                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TEAM  — $149/month (Control tier)  [Phase 1.8 unlock]         │
├─────────────────────────────────────────────────────────────────┤
│  Everything in Pro                                             │
│  🛡 Budget Governor toggle — ON                                 │
│  Set max cost/run + max retries per project                    │
│  "X runs blocked · $Y saved" dashboard                         │
│  Governs all developers on the team under shared rules         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ENTERPRISE  — Custom (Fabric tier) [Phase 1.9 unlock]         │
├─────────────────────────────────────────────────────────────────┤
│  Everything in Team                                            │
│  🧠 Context Memory toggle — ON                                  │
│  Caches stable context at $0.30/MTok vs $3.00/MTok (10×)      │
│  Savings compound every run — the retention moat               │
│  SLA: "your agent never exceeds your budget"                   │
│  Context memory is local, private, portable                    │
└─────────────────────────────────────────────────────────────────┘
```

### The upgrade trigger (why users pay)

Each gate fires at the exact moment the user wants to act:

```
Free user sees: "65% repeated tokens · ~$0.018/run savings available"
                [⚡ Enable Optimizer]  ← grayed, lock icon
                "Unlock with Pro — $49/mo"

At 100 runs/day that is $1.80/day = $54/month wasted.
Pro costs $49/month. ROI is positive on day 31. The math sells itself.
```

### The retention hook (why users stay)

```
Phase 1.7 (Pro):     Proof card per run → dev shares with manager
Phase 1.8 (Team):    Budget rules set once → never think about it again
Phase 1.9 (Fabric):  Context memory grows every run →
                     switching means losing your entire optimization history
```

### Revenue ladder

```
Phase 1.6 alone:  $0  — builds corpus of users who SEE the problem
Phase 1.7 (Pro):  $49/mo  × N solo devs     ← first revenue
Phase 1.8 (Team): $149/mo × N teams          ← 3× per account
Phase 1.9 (Ent):  Custom  × N companies      ← enterprise + moat
```

### Billing implementation

Phase 1 is single-tenant (one developer, one local Docker install). No Stripe, no auth,
no user table required yet. The `plan` field in the settings table is set manually
(or via a license key emailed to alpha users). When moving to multi-tenant SaaS, add
`user_id` + Stripe customer ID.

```sql
-- settings table includes:
plan TEXT DEFAULT 'free'
-- Values: 'free' | 'pro' | 'team' | 'enterprise'
-- Set manually for Phase 1 alpha; Stripe webhook sets it at scale
```

### Competitive moat summary

```
Langfuse:    OSS observability, no control plane
Helicone:    Proxy + caching, always-on, no per-feature toggles
Portkey:     Budget guardrails, config-file-first, no toggle UI
LangSmith:   Tracing only, SaaS-only, no optimization actions
Braintrust:  Eval + observability, no cost control plane

Agentium:    First toggle-based control plane where flipping a switch
             applies a measured optimization and shows before/after gains.
             "Free to observe. Pay only when you save."
```

---

## Phase 2: Agentic Inference System Blueprint Validation

Purpose:

Convert Phase 1 evidence into a validated runtime/compiler/backend/system/hardware architecture direction for agentic inference.

Phase 2 begins with workload modeling and market-available platform fit evaluation, then validates the blueprint through existing-backend/system evaluation, prototype measurements, trace replay simulation, and hardware primitive feasibility work.

Phase 2 final output:

```text
Agentic Inference System Blueprint Validation Package
```

The final package must include:

- agentic workload model
- system bottleneck map
- existing platform fit report
- existing backend/system gap report
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

  Inputs:

  - Phase 1.6 trace corpus
  - benchmark-style records
  - before/after pairs
  - evidence quality labels
  - Phase 2 handoff package

  Outputs:

  - workload taxonomy
  - agent loop shape model
  - bottleneck distribution
  - context lifetime model
  - retry/backtrack profile
  - model/tool/I/O/orchestration split

- **Phase 2.1 Existing Platform Fit Evaluation**
  Evaluate standard market-available systems against the Phase 2.0 workload model before choosing a backend experiment or architecture bet. This is a spec-based and evidence-labeled platform fit analysis, not a measured benchmark unless Phase 2.9 later runs the workload on the platform.

  Purpose:

  ```text
  Given the measured agentic workload shape, which existing platform class is the best first validation target?
  ```

  Candidate platform classes:

  - OpenAI/API baseline path where provider telemetry is limited
  - CPU-only or CPU-heavy orchestration baseline
  - high-memory CPU/DRAM systems for context-heavy control paths
  - NVIDIA H100/HGX H100 installed-base systems
  - NVIDIA H200/HGX H200 memory-capacity systems
  - NVIDIA B200/HGX B200 Blackwell systems
  - NVIDIA RTX PRO 6000 Blackwell Server Edition for lower-cost on-prem/dev validation
  - NVIDIA GB200/GB300 NVL72 rack-scale systems for high-concurrency or large-model north-star evaluation
  - cloud GPU instances that map to the above classes
  - future CXL/DRAM/NVMe memory-tier systems where available

  Required platform inventory fields:

  - CPU model and core count
  - GPU model and GPU count
  - GPU memory capacity and bandwidth
  - system RAM capacity and bandwidth where available
  - storage type and capacity
  - interconnect/fabric: PCIe, NVLink, NVSwitch, InfiniBand, Ethernet, CXL where available
  - OS and driver/CUDA stack
  - inference backend availability
  - model size and context length support
  - batching settings
  - prefix/KV cache support
  - telemetry availability
  - cost/accessibility

  Fit dimensions:

  - context/KV capacity
  - memory bandwidth
  - prefill-heavy workload fit
  - decode/interactive latency fit
  - CPU orchestration fit
  - queueing/batching fit
  - fabric/network fit
  - backend compatibility with vLLM, SGLang, LMCache, Dynamo-style routing, or equivalent stacks
  - telemetry observability
  - cost-to-validate
  - risk of overfitting to hyperscale-only systems

  Expected initial recommendation unless evidence changes:

  - Start serious Phase 2 validation on NVIDIA H200/HGX H200-class systems when available, because the memory capacity/bandwidth profile is more relevant to repeated-context and prefill-heavy agentic workloads than smaller installed-base GPUs.
  - Use RTX PRO 6000 Blackwell Server Edition-class systems as a lower-cost private/on-prem/developer validation tier when H200-class access is not practical.
  - Treat GB200/GB300 NVL72-class systems as a rack-scale north-star or high-concurrency validation target, not the first practical validation dependency.

  Outputs:

  - Existing Platform Fit Matrix
  - recommended first validation platform
  - platform risk register
  - platform-to-backend experiment map
  - spec-based recommendation confidence
  - explicit missing-measurement list

  Non-goals:

  - no hardware speedup claim
  - no benchmark result claim
  - no procurement recommendation without cost/access constraints
  - no assumption that the largest NVIDIA system is automatically best

- **Phase 2.2 Existing Backend/System Gap Analysis**
  Evaluate how far existing backend and system stacks go on the selected platform class or available platform: GPU baseline, vLLM-style prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, Dynamo-style routing, CPU orchestration, GPU utilization, queueing, batching, memory pressure, cache hit/miss behavior, and networking/fabric implications where available.

  Phase 2.2 has two levels:

  - **Phase 2.2A Gap Analysis Framework**
    Analyze workload artifacts, platform fit results, and imported telemetry. Produce backend/system gap findings or a test plan when telemetry is missing.

  - **Phase 2.2B-G Real Existing Backend/System Evaluation**
    Run or import real measurements for baseline GPU/CPU/backend behavior, vLLM-style prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, Dynamo-style cache-aware routing studies, queueing/batching, memory pressure, and fabric/network symptoms where available. Produce an Existing Backend/System Gap Report.

- **Phase 2.3 Runtime-System-Hardware Interface**
  Define hints/contracts the runtime must expose to backend, system, and hardware layers: execution graph ID, dependency graph, stable prefix ID, context block fingerprint, KV reuse distance, branch checkpoint ID, retry boundary, SLO/priority, prefill/decode class, cache retention hint, routing locality hint, queue/scheduler hint, and memory tier hint.

- **Phase 2.4 Memory/KV/Context Architecture**
  Define persistent context architecture: context working set, cache TTL, HBM/DRAM/CXL/NVMe/object storage placement, persistent KV/context storage, prefix matching, warm context tier, shared context accessibility, branch checkpointing, KV compression/decompression, and retention/eviction policy.

- **Phase 2.5 Agentic Compiler / Execution Graph Model**
  Define the compiler/runtime layer that coordinates the whole system: execution graph IR, static vs dynamic scheduling, cache/prefix planning, branch checkpoint planning, prefill/decode placement, memory-tier placement, tool-wait overlap, backend placement, and routing/cache locality decisions.

- **Phase 2.6 Agentic Inference System Blueprint v1**
  Produce the formal system blueprint: workload requirements, system bottleneck map, existing-platform gaps, runtime-system-hardware interface, memory/KV/context architecture, compiler model, Agent Silicon Blueprint hardware section, primitive ranking, architecture bet candidates, evidence confidence score, and do-not-build-yet list.

- **Phase 2.7 Architecture Bet Decision**
  Select the first concrete system architecture bet to validate. Candidate bets include Agent Context Memory Fabric, prefill/decode-aware serving path, graph-aware runtime scheduler, branch checkpoint runtime, or a narrower hardware primitive if system evidence justifies it. Output an Architecture Decision Memo with evidence, risks, alternatives, and go/no-go criteria.

  Phase 2.7 contains the architecture bet candidates as sub-tracks:

  - **Phase 2.7A Agent Context Memory Fabric**
    Lead system architecture bet. Priority P0. Focus: preserving, routing, and reusing agent context/KV state across execution graphs. It coordinates runtime hints, backend cache behavior, stable prefix reuse, reuse-distance-aware retention, HBM/DRAM/CXL/NVMe-style memory tiering, prefill/decode pressure, and possible future fabric/hardware primitives. This is the first bet to prototype in Phase 2.8 unless stronger evidence changes the decision.

  - **Phase 2.7B Prefill/Decode-Aware Serving Path**
    Supporting bet. Priority P1. Focus: separating or scheduling prefill-heavy and decode-heavy agent model calls differently. This supports the memory fabric because repeated context often appears as prefill pressure.

  - **Phase 2.7C Graph-Aware Runtime Scheduler**
    Supporting bet. Priority P1. Focus: using the agent execution graph, dependency graph, SLO/priority, queue state, and cache locality hints to schedule or route model calls. This supports the memory fabric by helping route future calls toward retained context.

  - **Phase 2.7D Branch Checkpoint Runtime**
    Deferred bet. Priority P2. Focus: preserving branch/retry state to reduce recomputation during backtracking. This needs a larger retry/backtrack corpus before becoming the lead bet.

  Phase 2.7 decision rule:

  ```text
  Select one lead bet, list supporting mechanisms, and defer bets that lack enough evidence.
  ```

- **Phase 2.8 Agent Context Memory Fabric Backend Prototype**
  Prototype the selected Phase 2.7 lead bet first, expected default: Phase 2.7A Agent Context Memory Fabric. Integrate or evaluate context/KV reuse behavior inside existing backend infrastructure such as vLLM prefix caching, SGLang/RadixAttention-style reuse, LMCache-style KV reuse, or Dynamo-style cache-aware routing. Measure real cache hit/miss, TTFT, prefill time, task latency, and task success. This is the first point where Agentium may claim measured backend KV/cache behavior, only for the backend tested.

- **Phase 2.9 Real System/Platform Benchmark**
  Run baseline vs optimized workloads on real system/platform stacks selected by Phase 2.1. Compare baseline GPU serving, cache-aware backend behavior, CPU orchestration impact, memory pressure, queueing/routing, and optional fabric/network implications where available. Measure task latency, GPU/CPU utilization, memory pressure, queue depth, TTFT, ITL, prefill/decode timing, cache hit/miss, cost/task where available, and task success preservation. This is the first point where Agentium may claim measured system/hardware improvement, only for the tested workload and platform.

- **Phase 2.10 Trace Replay System Simulator**
  Build a trace replay simulator for candidate system architectures. Model baseline GPU serving, GPU plus prefix cache, persistent context memory tiers, CPU orchestration improvements, prefill/decode disaggregation, HBM/DRAM/CXL/NVMe/object storage tiers, cache capacity, cache hit/miss assumptions, and sensitivity analysis. This supports system/hardware simulation claims but still does not prove real hardware speedup.

- **Phase 2.11 Hardware Primitive Microarchitecture Spec**
  Specify the strongest validated primitive only after system/platform evidence shows a specific unsolved gap worth hardware attention. Candidate primitives include a persistent KV/cache controller, context fingerprint matcher, branch checkpoint buffer, prefill/decode scheduler, memory-tier controller, or fabric/offload interface. Include data path, control path, interfaces, expected metrics, and validation plan.

- **Phase 2.12 RTL/FPGA Feasibility Spike**
  Optionally explore feasibility for one primitive only if Phase 2.8-2.11 justify it. Output may include a small RTL sketch, testbench, synthesis/FPGA feasibility notes, or partner evaluation. This is not complete chip design and must not claim production silicon readiness.

Claim ladder:

- After **Phase 2.1**: spec-based existing platform fit recommendation, not a measured benchmark.
- After **Phase 2.6**: evidence-backed agentic inference system blueprint.
- After **Phase 2.8**: measured backend KV/cache behavior, if validated on a real backend.
- After **Phase 2.9**: measured system/hardware improvement, if validated on a real system/platform.
- After **Phase 2.10**: trace replay simulation for candidate system/runtime/hardware architectures.
- After **Phase 2.11**: concrete hardware primitive specification.
- After **Phase 2.12**: RTL/FPGA feasibility direction, not production chip design.

Phase 2 must not:

- claim real system/hardware speedup without Phase 2.9 real system/platform measurement
- claim real KV-cache control without Phase 2.8 backend integration or measured backend cache telemetry
- claim hardware simulation before Phase 2.10 trace replay simulator exists
- claim RTL/FPGA feasibility before Phase 2.12 feasibility work exists
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
- existing platform fit evaluation
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
A Phase 1 feature is allowed only if it feeds one of Phase 2.0 through Phase 2.12.
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
- It defines Phase 2.1 as Existing Platform Fit Evaluation for standard market systems before backend experiments.
- It defines Phase 2.2 as Existing Backend/System Gap Analysis.
- It defines Phase 1.5 as Phase 2 Handoff Package.
- It defines Phase 1.6 as the Evidence Campaign.
- It defines Phase 2.8 through Phase 2.12 as validation/prototype/simulation/feasibility work.
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
