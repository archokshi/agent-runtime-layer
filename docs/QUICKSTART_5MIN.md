# Agentium — 5-Minute Quickstart

You will have a live dashboard showing your agent's token cost, repeated context,
bottlenecks, and optimization controls within 5 minutes.

---

## What you need

- Docker Desktop running
- Python 3.10+
- A coding agent: Codex CLI or Claude Code (or use the built-in demo)

---

## Step 1 — Start Agentium (1 minute)

```bash
git clone https://github.com/archokshi/agent-runtime-layer.git
cd agent-runtime-layer
docker compose up --build -d
```

Wait ~30 seconds for all three services to start, then verify:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

Open the dashboard:

```
http://localhost:4000
```

---

## Step 2 — See your first trace (1 minute)

**Option A — Use the built-in demo (fastest)**

Click **Start demo** on the homepage at `http://localhost:4000`.

This loads a real coding-agent trace showing model calls, tool waits, repeated
context, and cost breakdown. You will immediately see:

- 65% repeated tokens detected
- Tool wait consuming 40% of elapsed time
- $0.0142 estimated cost per run
- Ranked optimization recommendations

**Option B — Import your own trace**

```bash
curl -X POST http://localhost:8000/api/traces/import \
  -H "Content-Type: application/json" \
  --data-binary @examples/sample-traces/repeated-context-task.json
```

---

## Step 3 — Connect your agent (2 minutes)

### Claude Code

Install hooks in the repo where you run Claude Code:

```bash
cd packages/sdk-python
pip install -e .
agent-runtime integrations install claude-code --repo /path/to/your/repo
```

Run Claude Code normally. Every turn is captured automatically.

### Codex

```bash
agent-runtime integrations install codex --repo /path/to/your/repo
```

Run Codex normally. If hooks do not fire, import the session JSONL after the run:

```bash
agent-runtime codex-session ~/.codex/sessions/YYYY/MM/DD/rollout-....jsonl \
  --project my-project --upload
```

### Custom Python agent

```python
from agent_runtime_layer import AgentRuntimeTracer, prompt_hash

with AgentRuntimeTracer(task_name="my task") as trace:
    with trace.model_call(
        model="claude-sonnet-4-6",
        role="planner",
        estimated_input_tokens=12000,
    ) as call:
        # ... your model call here ...
        call.finish(input_tokens=12000, output_tokens=520, cost_dollars=0.02)

    with trace.tool_call(tool_name="terminal", command="pytest") as tool:
        tool.finish(status="success", exit_code=0)
```

---

## Step 4 — Enable optimizations (1 minute)

Go to `http://localhost:4000/settings` — the Control Plane.

You will see three toggles showing your own run data as the value:

```
⚡ Context Optimizer   "65% repeated tokens → ~$0.018 saving/run"
🛡 Budget Governor     "3 retries detected → ~$0.009 wasted"
🧠 Context Memory      "65% tokens re-sent every call → cacheable"
```

**To unlock features for local testing:**

1. Scroll to the **Developer** section at the bottom of the Settings page
2. Select your plan (`pro` unlocks Optimizer, `team` unlocks Budget, `enterprise` unlocks Memory)
3. Flip the toggles ON
4. Click **Save changes**

Dashboard shows: *"Changes active — will apply from your next run"*

Run your agent again. Come back to `http://localhost:4000/overview` and the
**Gains since enabled** card will show your before/after delta:

```
Tokens      48,200 → 27,400    −43%  ✓
Cost/run    $0.0142 → $0.0081  −43%  ✓
Retries     3 → 0              −100% ✓
```

---

## What you get

| Page | What it shows |
|---|---|
| `/overview` | Agent health, time split, gains since optimizations enabled |
| `/runs` | All traced runs — status, cost, retries, repeated context % |
| `/runs/<id>` | Waterfall timeline, context growth, event feed, proof card |
| `/bottlenecks` | Where is time going — model vs tool vs idle |
| `/context` | Which tokens are re-sent on every call |
| `/cost` | Cost per task, per failure, before/after comparison |
| `/recommendations` | Ranked action list — what to fix first |
| `/settings` | Control Plane — enable optimizations, set budget limits |

---

## Pricing

| Tier | Price | What's unlocked |
|---|---|---|
| **Observe** | Free | Full dashboard — unlimited traces, all analysis |
| **Pro** | $49/mo | ⚡ Context Optimizer — auto-fix + proof card per run |
| **Team** | $149/mo | 🛡 Budget Governor — cost caps + retry limits |
| **Enterprise** | Custom | 🧠 Context Memory — persistent caching, compounding savings |

Free to observe. Pay only when you save.

---

## Troubleshooting

**Backend not starting**

```bash
docker compose logs backend
```

Check that port 8000 is free. SQLite data is stored in `backend/data/`.

**No events captured from Claude Code hooks**

```bash
agent-runtime integrations status claude-code --repo .
```

On Windows, hooks must use the full Python path. Run:

```bash
agent-runtime integrations install claude-code --repo . --global
```

**Settings page shows all toggles locked**

Open the Developer section at the bottom, select a plan, and save.
In production, plan is set via billing. Locally, you set it yourself.

**Dashboard shows no data after running agent**

Verify the backend is reachable:

```bash
curl http://localhost:8000/api/tasks
```

Check that `AGENT_RUNTIME_API_BASE` is not overriding the default
`http://localhost:8000/api` in your environment.

---

## Next steps

- [Architecture](ARCHITECTURE.md)
- [Claude Code integration](integrations/claude-code.md)
- [Codex integration](integrations/codex.md)
- [Full roadmap](AGENTIUM_PHASE_ROADMAP.md)
