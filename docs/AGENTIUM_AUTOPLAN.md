# Agentium Autoplan Review

Date: 2026-05-15
Repo: `C:\Users\trive\OneDrive\Desktop\Moonshot\Agentium\Codex_Dev\agent-runtime-layer`
Branch: `main`

## Scope

This autoplan pass reviewed the current Agentium repo as a product and engineering plan, using:

- `README.md`
- `AGENTS.md`
- `docs/BUILD_PLAN.md`
- `docs/AGENTIUM_PHASE_ROADMAP.md`
- `docs/VERSION_ROADMAP.md`
- `docs/ACCEPTANCE_TESTS.md`
- `docker-compose.yml`
- Backend API entrypoint
- Frontend package scripts
- Customer dashboard package scripts
- Current git status

The repo currently presents Agentium as a local-first profiler and control plane for coding agents:

> See it. Fix it. Control it. Remember it.

The canonical roadmap source of truth is `docs/VERSION_ROADMAP.md`, and it states the current implemented version is v5.0.

## Scope Guard

Current scope is **Agent Runtime Layer only**.

For now, Agentium should stay focused on Phase 1:

- tracing coding-agent runs
- importing/capturing agent execution events
- analyzing cost, latency, retries, context reuse, tool wait, and bottlenecks
- producing evidence-quality labels
- generating optimization recommendations
- validating before/after runtime improvements where possible
- packaging evidence for future Phase 2 work

The silicon, hardware, backend-system architecture, and broader agentic inference system blueprint work is **post-Phase 1**. It should remain a later direction that consumes Phase 1 evidence, not something the current sprint tries to build or claim.

Plain rule:

> Phase 1 measures the agent loop. Phase 2 interprets that evidence for system and silicon direction.

## Verification Run

Commands run:

```powershell
npm.cmd run build
```

in:

- `frontend`
- `customer-dashboard`
- `customer-dashboard-v3`

Results:

| Area | Result |
| --- | --- |
| `frontend` build | Passed |
| `customer-dashboard` build | Passed |
| `customer-dashboard-v3` build | Failed to start: `next` not installed in that package folder |
| Backend tests | Not run: `python` / `py -3` not available on current PATH |

Current git status:

```text
?? .claude/
```

No tracked source changes were present before this autoplan report was added.

## CEO Review

### Verdict

Proceed, but focus the next sprint on trust, verification, and a single canonical user journey.

Agentium has a compelling thesis: coding agents are not simple prompt-response workloads. They are execution graphs with loops, tool calls, waits, retries, repeated context, cache opportunities, orchestration overhead, and backend/hardware implications.

The product is strongest when it stays grounded in measured local evidence:

1. Capture a real agent run.
2. Show where time and money went.
3. Recommend one concrete optimization.
4. Apply or simulate the optimization.
5. Show proof without overclaiming.

The roadmap is ambitious and coherent, but the repo now has many phases, dashboards, docs, and validation surfaces. The buyer/user story can get blurry unless the next sprint compresses the experience into one highly reliable demo path.

### Best v5.0 Product Claim

Agentium is a local-first profiler and control plane for coding agents that turns agent traces into measurable runtime, cost, context, and backend optimization evidence.

### Primary User

Start with developers and AI infrastructure teams who are already running coding agents and asking:

- Why is this run slow?
- Why did cost spike?
- Where are retries happening?
- How much context is repeated?
- What should we optimize first?
- Which runtime/backend/hardware bottleneck does real evidence suggest?

### Strategic Risk

The largest risk is overclaiming the silicon/hardware direction before measured backend or hardware evidence exists.

The docs mostly handle this well with no-overclaiming boundaries. Keep that discipline. The product should keep saying "evidence-backed blueprint" rather than "we proved hardware speedup" unless a real backend/hardware test supports it.

## Design Review

### Verdict

The dashboard should behave like an operator cockpit, not a marketing site.

The key experience should be dense, sequential, and proof-oriented:

1. Import or capture trace
2. Open run
3. See timeline and bottleneck
4. See repeated-context/cost waste
5. Apply or simulate optimization
6. Export proof or handoff package

### UI Scope

There are three frontend surfaces:

- `frontend`
- `customer-dashboard`
- `customer-dashboard-v3`

This is the biggest design/product alignment issue. If all three are active, the docs should clearly state:

- which dashboard is canonical for users
- which dashboard is experimental
- which ports map to which audience
- which one should be used in demos

Current README points users to `http://localhost:4000` as the Agentium dashboard, while `docker-compose.yml` also exposes `frontend` on 3000 and v3 dashboard on 4001. That is workable, but only if the README and quickstart make the intended path unmistakable.

### Recommended Demo Flow

Use this as the canonical demo:

1. `docker compose up --build -d`
2. Open `http://localhost:4000`
3. Import sample trace
4. Open `/runs`
5. Open a run detail page
6. Show waterfall, context waste, cost, and recommendation
7. Toggle Control Plane setting
8. Show before/after or proof card

Keep Phase 2 / Silicon Blueprint material as a second-act narrative after the user trusts the trace profiler.

## Engineering Review

### Verdict

The codebase has broad coverage and appears structurally mature, but the next engineering priority is reproducibility.

The frontend/customer-dashboard builds passed, which is good. The v3 dashboard dependency gap and unavailable Python runtime are current local verification blockers.

### Architecture Snapshot

```text
Coding agents / SDK / imports
  -> FastAPI backend
  -> SQLite local persistence
  -> analyzer / optimizer / scheduler / telemetry / blueprint modules
  -> Next.js dashboards
  -> local docs, validation reports, and handoff artifacts
```

Primary backend app:

- `backend/app/main.py`

Included API routers:

- health
- tasks
- events
- traces
- analysis
- blueprints
- platform
- validation
- benchmarks
- phase1_exit
- corpus
- evidence
- evidence_campaign
- phase2_handoff
- telemetry
- optimization
- budget
- context_memory
- settings

This lines up with the v5.0 roadmap.

### P0 Before Next Demo

1. Fix `customer-dashboard-v3` install/build reproducibility.

The build failed because `next` was unavailable in that folder. Either install dependencies there, add/commit the lockfile if missing, or mark v3 as experimental and remove it from the default Docker/demo path.

2. Restore backend test availability.

The documented validation depends on `python -m pytest backend/tests`, but Python was not available on this machine/path. Add a Windows-friendly setup note or use Docker-based test commands so validation does not depend on host Python.

3. Clarify canonical dashboard.

Choose the default:

- Port 4000 customer dashboard for demos, or
- Port 3000 full platform dashboard

Then make README, quickstart, and Docker comments match.

4. Keep `.claude/` intentionally scoped.

`.claude/` is untracked. If it is intended project configuration, document it and commit it. If it is local-only, add the appropriate ignore rule.

### P1 Before Shipping The Next Sprint

1. Add one command or script for local verification.

Recommended:

```powershell
.\scripts\check-local.ps1
```

It should run:

- backend tests, preferably in Docker if host Python is absent
- `frontend` build
- `customer-dashboard` build
- optional `customer-dashboard-v3` build only if enabled
- Docker health smoke test

2. Add a "current version validation matrix" to docs.

Each row should cover:

- v5.0 feature
- API endpoint
- dashboard route
- test file
- sample fixture
- current status

3. Separate projection from measurement in UI labels.

The roadmap already draws this boundary. Make sure every dashboard card uses labels like:

- measured
- estimated
- inferred
- projection-only
- missing evidence

4. Keep Phase 2 handoff generated from evidence, not aspirations.

Phase 1 exists to produce evidence Phase 2 consumes. Any Phase 2 recommendation should cite the trace, telemetry, benchmark, or evidence-quality source behind it.

## Developer Experience Review

### Verdict

The docs are rich, but the repo needs a sharper "one golden path" for a new developer.

The current README is strong at product framing. The next DX improvement is reducing setup ambiguity.

### Recommended Golden Path

Add or tighten a quickstart around:

```powershell
docker compose up --build -d
curl.exe http://localhost:8000/api/health
```

Then:

- open `http://localhost:4000`
- import sample trace
- open run detail
- verify recommendation/proof flow

### DX Gaps

1. Host Python absence breaks documented tests.

Use Docker-based validation or add exact Windows setup instructions.

2. Multiple dashboards create uncertainty.

Document "use this one first" prominently.

3. v3 dashboard dependency state is unclear.

It has `package.json` but no local `next` executable during build. Decide whether it is part of the supported local setup.

4. `.claude/` is untracked.

Treat it as either product config or local-only state.

## Autoplan Decisions

| Decision | Classification | Recommendation | Reason |
| --- | --- | --- | --- |
| Keep v5.0 roadmap as source of truth | Mechanical | Accept | `AGENTS.md` explicitly points to `docs/VERSION_ROADMAP.md` |
| Use customer dashboard on port 4000 as default demo | Taste | Recommend | README already points there, and build passed |
| Treat v3 dashboard as experimental until build is fixed | Mechanical | Accept | Current build cannot find `next` |
| Prioritize verification over new features | Mechanical | Accept | Product surface is already broad; trust is the bottleneck |
| Continue no-overclaiming hardware language | Mechanical | Required | The roadmap depends on measured evidence boundaries |
| Add Docker-based backend test command | Mechanical | Recommend | Host Python is unavailable locally |

## Next Sprint Plan

### Phase 1: Reproducibility

- Decide whether `customer-dashboard-v3` is supported or experimental.
- Fix/install v3 dependencies if supported.
- Add a Windows-friendly verification command.
- Add Docker-based backend test instructions.
- Confirm Docker Compose starts all supported services.

### Phase 2: Canonical Demo Path

- Update README/quickstart to identify the primary dashboard.
- Add a short "demo this first" path.
- Make sample trace import and run-detail flow obvious.
- Ensure every demo claim maps to measured, estimated, inferred, or projection-only evidence.

### Phase 3: Evidence Integrity

- Add or refresh the v5.0 validation matrix.
- Link every Phase 2 handoff section to its evidence source.
- Audit UI cards for overclaiming language.
- Keep official benchmark claims explicitly marked as not-yet-run unless verified.

### Phase 4: Ship Readiness

- Run full Docker smoke test.
- Run backend tests through Docker or installed Python.
- Run supported frontend builds.
- Run `/gstack-review`.
- Run `/gstack-qa` against the running local app.

## Final Recommendation

Agentium is in a strong but broad state. The next best move is not another feature layer. It is to make the current v5.0 path boringly reproducible:

```text
docker compose up -> open dashboard -> import/capture trace -> inspect bottleneck -> see recommendation -> verify proof/evidence boundary
```

Once that path is reliable, the Phase 2 blueprint story becomes much more credible because it rests on a traceable evidence chain.
