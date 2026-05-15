# Agentium — Validation Matrix (v5.0)

This matrix maps every product capability to its API endpoint, dashboard route,
evidence quality level, and current verification status.

Run `.\scripts\check-local.ps1` to verify all green items are live.

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Verified — works, tested, confirmed |
| ⚠️ | Estimated — works but not independently measured |
| 🔒 | Gated — requires plan upgrade to activate |
| ❌ | Not implemented / not verified |

---

## Core Observability

| Feature | API Endpoint | Dashboard Route | Evidence | Status |
|---|---|---|---|---|
| Health check | `GET /api/health` | — | — | ✅ |
| List all runs | `GET /api/tasks` | `/runs` | — | ✅ |
| Run detail | `GET /api/tasks/{id}` | `/runs/{id}` | — | ✅ |
| Event feed | `GET /api/tasks/{id}/events` | `/runs/{id}` → event feed | Measured | ✅ |
| Analysis report | `GET /api/tasks/{id}/analysis` | `/bottlenecks`, `/cost` | Estimated | ✅ |
| Bottleneck detection | `GET /api/tasks/{id}/analysis` | `/bottlenecks` | Estimated | ✅ |
| Context inspector | `GET /api/tasks/{id}/optimized-context` | `/context` | Estimated | ✅ |
| Cost explorer | `GET /api/tasks/{id}/analysis` | `/cost` | Estimated | ✅ |
| Ranked recommendations | `GET /api/tasks/{id}/optimizations` | `/recommendations` | Inferred | ✅ |
| Platform summary | `GET /api/platform/summary` | `/overview` | Estimated | ✅ |
| Waterfall timeline | Derived from events | `/runs/{id}` | Measured | ✅ |
| Import trace (JSON) | `POST /api/traces/import` | `/import` | — | ✅ |

---

## Claude Code Integration

| Feature | Command | Hook Type | Status |
|---|---|---|---|
| Install hooks | `agent-runtime integrations install claude-code --repo .` | `.claude/settings.json` | ✅ |
| Capture prompt | — | `UserPromptSubmit` | ✅ |
| Capture tool use | — | `PreToolUse`, `PostToolUse` | ✅ |
| Capture stop | — | `Stop` | ✅ |
| Remove hooks | `agent-runtime integrations uninstall claude-code --repo .` | — | ✅ |

---

## Codex Integration

| Feature | Command | Hook Type | Status |
|---|---|---|---|
| Install hooks | `agent-runtime integrations install codex --repo .` | Codex config | ✅ |
| Session JSONL import | `agent-runtime codex-session <path> --upload` | — | ✅ |

---

## Context Optimizer (Pro)

| Feature | API Endpoint | Dashboard Route | Evidence | Status |
|---|---|---|---|---|
| Apply optimization | `POST /api/tasks/{id}/apply-optimization` | `/runs/{id}` → Apply button | Measured | ✅ |
| Proof record stored | `GET /api/optimization-proofs` | `/runs/{id}` → Proof card | Measured | ✅ |
| Auto-optimize SDK flag | `_load_remote_settings()` in tracer | `/settings` → toggle | Measured | ✅ |
| Gains since enabled card | Derived from baseline snapshot | `/overview` | Measured | ✅ |
| Token reduction −43% | `OptimizationProofRecord` | Proof card | Measured ✓ Verified | ✅ |
| Cost reduction −43% | `OptimizationProofRecord` | Proof card | Measured ✓ Verified | ✅ |
| Plan gate (Pro required) | `PATCH /api/settings` → 403 | `/settings` → lock icon | — | ✅ |

---

## Budget Governor (Team)

| Feature | API Endpoint | Dashboard Route | Evidence | Status |
|---|---|---|---|---|
| Get/set budget config | `GET/POST /api/budget/config` | `/settings` → toggle + inputs | — | ✅ |
| Budget summary | `GET /api/budget/summary` | `/overview` → Budget card | Measured | ✅ |
| Hook enforcement (PreToolUse) | SDK `check_budget()` | — | Measured | ✅ |
| Block on cost exceeded | Returns `blocked=true` in hook | — | Measured | ✅ |
| Block on retry exceeded | Returns `blocked=true` in hook | — | Measured | ✅ |
| Budget events stored | `POST /api/budget/events` | `/overview` → Budget card | Measured | ✅ |
| Plan gate (Team required) | `PATCH /api/settings` → 403 | `/settings` → lock icon | — | ✅ |

---

## Context Memory (Enterprise)

| Feature | API Endpoint | Dashboard Route | Evidence | Status |
|---|---|---|---|---|
| Context memory summary | `GET /api/context-memory/summary` | `/overview` → Memory card | Estimated | ✅ |
| Context memory upsert | `POST /api/context-memory` | — | — | ✅ |
| Local proxy startup | `agent-runtime proxy --port 8100` | `/settings` → toggle | Measured | ✅ |
| SHA-256 fingerprinting | `proxy.py` | — | Measured | ✅ |
| cache_control injection | `proxy.py` → Anthropic API | — | Measured | ⚠️ |
| Cache savings tracking | `context_memory.cache_savings_dollars` | `/overview` | Estimated | ⚠️ |
| Plan gate (Enterprise required) | `PATCH /api/settings` → 403 | `/settings` → lock icon | — | ✅ |

---

## Control Plane (All tiers)

| Feature | API Endpoint | Dashboard Route | Status |
|---|---|---|---|
| Get settings | `GET /api/settings` | `/settings` | ✅ |
| Update settings | `PATCH /api/settings` | `/settings` → Save | ✅ |
| Plan gate enforcement | `PLAN_GATES` dict → 403 | `/settings` → lock icon | ✅ |
| SDK reads settings on init | `_load_remote_settings()` | — | ✅ |
| Baseline snapshot on first enable | stored in `settings` table | `/overview` → Gains card | ✅ |
| Gains since enabled delta | Derived from `enabled_at` | `/overview` | ✅ |

---

## Dashboard Routes (port 4001 — canonical)

| Route | What it shows | Status |
|---|---|---|
| `/overview` | Hero savings, metric cards, gains since enabled, time split, patterns | ✅ |
| `/runs` | All traced runs, ⚡ Fix it badges, stat chips | ✅ |
| `/runs/{id}` | Waterfall, context growth, event feed, proof card, recommendations | ✅ |
| `/settings` | Control Plane — 3 toggles, plan gates, developer override | ✅ |
| `/bottlenecks` | Time split breakdown, bottleneck cards | ✅ |
| `/context` | Repeated token analysis, stable block list | ✅ |
| `/cost` | Cost per run, cost per failure, before/after | ✅ |
| `/recommendations` | P0/P1/P2 ranked action cards | ✅ |

---

## Infrastructure

| Item | Details | Status |
|---|---|---|
| Backend Docker image | `archokshi/backend:latest` on Docker Hub | ✅ |
| Dashboard Docker image | `archokshi/dashboard:latest` on Docker Hub | ✅ |
| Install script | `agent-runtime-layer.vercel.app/install.sh` | ✅ |
| Install page | `agent-runtime-layer.vercel.app` | ✅ |
| docker-compose.yml | 4 services: backend, frontend, customer-dashboard, customer-dashboard-v3 | ✅ |
| SQLite persistence | `backend/data/` volume mounted | ✅ |
| Local npm build (v3) | `package-lock.json` committed | ✅ |

---

## Evidence Quality Summary

| Category | Level | Notes |
|---|---|---|
| Token reduction −43% | ✓ Measured | Real before/after `OptimizationProofRecord` |
| Cost reduction −43% | ✓ Measured | Same proof record |
| Repeated context % | ~ Estimated | From trace event attributes |
| Tool wait % | ~ Estimated | Derived from timing gaps |
| Cache savings (proxy) | ~ Estimated | Estimated from cache_control hits |
| Retry waste $ | ~ Estimated | retry_count × avg_cost heuristic |
| Budget blocks | ✓ Measured | Stored in `budget_events` table |

---

## Known Gaps

| Gap | Priority | Action |
|---|---|---|
| Backend tests require Python on host | P1 | Use Docker-based test command |
| cache_control hit rate not yet confirmed from real Anthropic response | P1 | Run proxy against real API call |
| No official SWE-bench or benchmark traces yet | P2 | Capture with controlled benchmark task |
| Context Memory savings not yet independently verified | P2 | Run proxy, record `cache_read_input_tokens` from API response |

---

*Last updated: 2026-05-15 · Agentium v5.0*
