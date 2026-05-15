# Agentium — 5-Minute Quickstart

See exactly what your coding agent costs, where it stalls, and what to fix —
in under 5 minutes.

---

## What you need

- macOS, Linux, or Windows (WSL / Git Bash / PowerShell)
- A coding agent: Claude Code or Codex CLI

That's it. Docker is installed automatically if you don't have it.

---

## Step 1 — Install Agentium (1 minute)

**macOS / Linux / WSL / Git Bash**

```bash
curl -sSL https://agent-runtime-layer.vercel.app/install.sh | bash
```

The installer:
1. Checks for Docker — installs it automatically if missing
2. Pulls the Agentium backend and dashboard images
3. Starts all services
4. Opens `http://localhost:4001` in your browser

**Windows (PowerShell)**

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) first, then:

```powershell
curl.exe -O https://agent-runtime-layer.vercel.app/docker-compose.yml
docker compose up -d
Start-Process "http://localhost:4001"
```

**Verify it's running:**

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

## Step 2 — See your first trace (1 minute)

Open `http://localhost:4001/runs`

Click **Import demo trace** — this loads a real coding-agent session showing:

- Token cost breakdown per model call
- Tool wait time (how long your agent sits idle)
- Repeated context percentage (tokens re-sent every call)
- Ranked recommendations for what to fix first

You'll see a live run in under 30 seconds without needing to connect your agent yet.

---

## Step 3 — Connect Claude Code (2 minutes)

Install the Python SDK:

```bash
pip install agent-runtime-layer
```

Install hooks in the repo where you run Claude Code:

```bash
agent-runtime integrations install claude-code --repo /path/to/your/repo
```

Run Claude Code normally. Every prompt → tool call → response is captured
automatically. No code changes required.

Check capture is working:

```bash
agent-runtime integrations status claude-code --repo /path/to/your/repo
```

Open `http://localhost:4001/runs` — your run appears within seconds of the
Claude Code session ending.

### Connecting Codex instead

```bash
agent-runtime integrations install codex --repo /path/to/your/repo
```

Or import a past session directly:

```bash
agent-runtime codex-session ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl \
  --project my-project --upload
```

---

## Step 4 — Enable optimizations (1 minute)

Open `http://localhost:4001/settings`

Three toggles are ready — your plan is already set to **Pro** so all features
are unlocked for the alpha period:

| Toggle | What it does |
|---|---|
| ⚡ **Context Optimizer** | Strips repeated tokens before each model call. One click. |
| 🛡 **Budget Governor** | Blocks runaway runs when cost or retries exceed your limit |
| 🧠 **Context Memory** | Caches stable context across sessions — eliminates cold-start cost |

Flip **Context Optimizer** on → **Save changes**.

Run your agent again. Open `http://localhost:4001/overview` — the
**Gains since enabled** card shows your before/after:

```
Tokens      48,200 → 27,400    −43%
Cost/run    $0.0142 → $0.0081  −43%
Retries     3 → 0              −100%
```

---

## Dashboard pages

| Page | What it shows |
|---|---|
| `/overview` | Savings summary, time split, gains since optimizations enabled |
| `/runs` | Every traced run — cost, retries, repeated context %, Fix-it badges |
| `/runs/<id>` | Waterfall timeline, context growth, event feed, proof card |
| `/bottlenecks` | Where time goes — model vs tool vs idle |
| `/context` | Which tokens are re-sent on every call |
| `/cost` | Cost per task, per failure, before/after comparison |
| `/recommendations` | Ranked action list — what to fix first |
| `/settings` | Control Plane — toggles, budget limits, plan |

---

## Troubleshooting

**Services not starting**

```bash
docker compose -f ~/.agentium/docker-compose.yml logs backend
```

Port 8000 or 4001 already in use? Stop whatever is running on those ports.

**No runs appear after running Claude Code**

```bash
agent-runtime integrations status claude-code --repo .
```

On Windows (native PowerShell, not WSL), hooks need the full Python path:

```powershell
agent-runtime integrations install claude-code --repo . --global
```

**Python not found**

```bash
# macOS
brew install python

# Ubuntu / Debian
sudo apt install python3 python3-pip

# Then install the SDK
pip install agent-runtime-layer
```

**All toggles show as locked**

Go to `/settings` → Developer section → select plan `pro` → Save.
(Alpha users: this should already be set. If not, this is the fix.)

---

## Getting help

Email: optiinfra@gmail.com
Install page: https://agent-runtime-layer.vercel.app
