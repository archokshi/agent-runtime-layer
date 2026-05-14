# Agentium — Agent Runtime Layer

**See it. Fix it. Control it. Remember it.**

Agentium is a self-hosted profiler and control plane for coding agents.
It captures every model call, tool wait, retry, and context re-send — then gives
you one-click controls to optimize them.

```
Free to observe. Pay only when you save.
```

---

## Preview

![Agentium — what happens inside a real coding agent run](docs/assets/dashboard-overview.svg)

---

## The Problem

Every coding agent run wastes money and time in four ways:

| Waste | Typical impact | What Agentium does |
|---|---|---|
| Repeated context | 40–70% of input tokens re-sent every call | Strips stable context automatically |
| Retry spirals | 3–10 retries at full cost before giving up | Caps retries and cost per run |
| Cold-start cost | Same system prompt billed at $3/MTok every run | Caches at $0.30/MTok via proxy |
| No visibility | You don't know what the agent is doing or why | Full waterfall + event feed |

---

## How It Works

```
Step 1 — See it      Install hooks or SDK → dashboard shows token waste, cost, bottlenecks
Step 2 — Fix it      Click Apply on any run → proof card shows −43% tokens, −43% cost
Step 3 — Control it  Set budget cap → hooks block runaway runs automatically
Step 4 — Remember it Proxy caches stable context → savings compound every run
```

One Control Plane page. Three toggles. Active from your next run.

---

## Quickstart

```bash
git clone https://github.com/archokshi/agent-runtime-layer.git
cd agent-runtime-layer
docker compose up --build -d
```

Open:

```
http://localhost:4000          ← Agentium dashboard
http://localhost:8000/docs     ← API
```

→ **[Full 5-minute guide](docs/QUICKSTART_5MIN.md)**

---

## Integrations

### Claude Code

```bash
cd packages/sdk-python && pip install -e .
agent-runtime integrations install claude-code --repo /path/to/your/repo
```

Run Claude Code normally. Every turn is captured.

### Codex

```bash
agent-runtime integrations install codex --repo /path/to/your/repo
```

Or import a session after the run:

```bash
agent-runtime codex-session ~/.codex/sessions/YYYY/MM/DD/rollout-....jsonl \
  --project my-project --upload
```

### Custom Python agent

```python
from agent_runtime_layer import AgentRuntimeTracer

with AgentRuntimeTracer(task_name="my task") as trace:
    with trace.model_call(model="claude-sonnet-4-6", role="planner",
                          estimated_input_tokens=12000) as call:
        call.finish(input_tokens=12000, output_tokens=520, cost_dollars=0.02)

    with trace.tool_call(tool_name="terminal", command="pytest") as tool:
        tool.finish(status="success", exit_code=0)
```

Settings from the Control Plane apply automatically on tracer init — no code
changes needed after you flip a toggle.

---

## Dashboard

| Route | What it shows |
|---|---|
| `/overview` | Agent health, time split, detected patterns, gains since optimizations enabled |
| `/runs` | All traced runs — status, cost, retries, repeated context %, optimize badge |
| `/runs/<id>` | Waterfall timeline, context growth, event feed, Apply Optimization button |
| `/bottlenecks` | Where time goes — model vs tool wait vs idle |
| `/context` | Which tokens are re-sent on every call — stable vs dynamic breakdown |
| `/cost` | Cost per task, cost per failure, before/after comparison |
| `/recommendations` | Ranked action list — what to fix first with impact scores |
| `/settings` | **Control Plane** — enable optimizations, set budget limits, see pricing |

---

## Control Plane

Go to `http://localhost:4000/settings`.

Each toggle shows your own run data as the value proposition before you enable it:

```
⚡ Context Optimizer    [toggle]
   "Your runs waste 65% repeated tokens → ~$0.018 saving/run"

🛡 Budget Governor     [toggle]   max cost: $0.10   max retries: 3
   "3 retries detected this week → ~$0.009 wasted"

🧠 Context Memory      [toggle]
   "65% tokens re-sent every call → cacheable at 10× cheaper rate"
```

Flip a toggle → Save → run your agent again → the **Gains since enabled** card
on `/overview` shows the before/after delta with real measured numbers.

---

## Pricing

| Tier | Price | Unlocks |
|---|---|---|
| **Observe** | Free | Full dashboard — unlimited traces, all analysis pages |
| **Pro** | $49/mo | ⚡ Context Optimizer — auto-fix + proof card per run |
| **Team** | $149/mo | 🛡 Budget Governor — cost caps + retry limits across all runs |
| **Enterprise** | Custom | 🧠 Context Memory — persistent cache, compounding savings, SLA |

For local alpha testing, set your plan in the Developer section of `/settings`.

---

## Architecture

```
Coding agents
  Codex (hooks) · Claude Code (hooks) · Custom agents (Python SDK) · Imported traces
        │
        ▼
FastAPI + SQLite                    ← localhost:8000
  Trace ingestion · Analysis · Optimization · Budget · Context Memory · Settings
        │
        ▼
Agentium dashboard (Next.js)        ← localhost:4000
  Overview · Runs · Bottlenecks · Context · Cost · Recommendations · Settings
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## What Agentium Does Not Claim

- No real KV-cache control (uses Anthropic prefix caching, not custom backend)
- No hardware simulation or speedup claims
- No production authentication or billing (self-hosted, local by design)
- No official SWE-bench results

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

---

## Documentation

| Doc | What it covers |
|---|---|
| [5-minute quickstart](docs/QUICKSTART_5MIN.md) | Install → first trace → Control Plane |
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Phase roadmap](docs/AGENTIUM_PHASE_ROADMAP.md) | Full product and monetization roadmap |
| [Claude Code integration](docs/integrations/claude-code.md) | Hook setup and validation |
| [Codex integration](docs/integrations/codex.md) | Hook setup and JSONL import |
| [API spec](docs/API_SPEC.md) | All endpoints |
| [Trace schema](docs/TRACE_SCHEMA.md) | Event format |
| [Security and privacy](docs/SECURITY_PRIVACY.md) | Local data handling |
| [Limitations](docs/LIMITATIONS.md) | What is and is not claimed |

---

## Validation

```bash
# Backend tests
cd backend && PYTHONPATH=. python -m pytest tests

# Docker smoke test
docker compose up --build -d
curl http://localhost:8000/api/health   # → {"status":"ok"}
curl http://localhost:8000/api/settings # → {"plan":"free",...}
```

---

## Privacy

All data stays local. SQLite only. No telemetry. Obvious secrets are redacted
before persistence. Review traces before sharing them publicly.

---

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).

Free to use, self-host, modify, and contribute under the GNU Affero General
Public License v3.0 or later. Commercial licensing available for teams that need
proprietary embedding, hosted-service use, or custom terms.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
