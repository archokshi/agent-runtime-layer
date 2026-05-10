# Codex Native Capture

Agent Runtime Layer can capture Codex coding-agent runs through Codex hooks.

This integration is part of Phase 1.6A: Codex Native Capture. It is designed to collect real coding-agent evidence for the Phase 1.6 Evidence Campaign and Phase 2 handoff package.

## Prerequisites

- Docker Desktop running (backend on port 8000, dashboards on ports 3000 and 4000)
- Python 3.10+
- [Codex CLI](https://github.com/openai/codex) installed
- `agent-runtime` CLI installed:

```bash
cd packages/sdk-python
pip install -e .
```

On Windows (PowerShell):

```powershell
cd packages\sdk-python
pip install -e .
```

## What It Captures

- Codex session metadata
- user prompt / turn start
- tool-call start and end
- terminal command evidence when exposed by the hook payload
- file-change evidence when exposed by the hook payload
- task end / stop event
- post-run Codex session JSONL when live hooks are unavailable

## Quickstart

### macOS / Linux

Start Agent Runtime Layer:

```bash
docker compose up --build
```

Install repo-local Codex hooks inside the repository where you run Codex:

```bash
agent-runtime integrations install codex --repo .
```

For live validation, global install is often more reliable because it does not depend on project-local `.codex/` trust:

```bash
agent-runtime integrations install codex --global
```

Run Codex normally in that repository. Open the customer dashboard:

```text
http://localhost:4000
```

Each captured Codex turn appears as a task trace. The developer dashboard (with full analysis) is at:

```text
http://localhost:3000
```

### Windows

Start Agent Runtime Layer (PowerShell):

```powershell
docker compose up --build
```

Install repo-local Codex hooks:

```powershell
agent-runtime integrations install codex --repo .
```

For global install (recommended on Windows):

```powershell
agent-runtime integrations install codex --global
```

Run Codex normally. Open the dashboard:

```text
http://localhost:4000
```

On Windows, the global hook command is automatically generated as a PowerShell command so no additional shell configuration is needed.

## Reliable Fallback: Import Codex Session JSONL

Some Codex CLI modes may not fire hooks on every platform. If a real Codex run completes but no task appears in the dashboard, import the Codex session JSONL after the run:

**macOS / Linux:**

```bash
agent-runtime codex-session ~/.codex/sessions/YYYY/MM/DD/rollout-....jsonl --project codex-live --upload
```

**Windows:**

```powershell
agent-runtime codex-session C:\Users\<you>\.codex\sessions\YYYY\MM\DD\rollout-....jsonl --project codex-live --upload
```

The fallback importer converts the completed Codex session into an Agent Runtime trace, writes it to `.agent-runtime/traces/`, and uploads it when `--upload` is provided. This is post-run capture, not live streaming.

## Status

Check whether hooks are installed:

```bash
agent-runtime integrations status codex --repo .
```

For global hooks:

```bash
agent-runtime integrations status codex --global
```

Remove Agent Runtime hooks:

```bash
agent-runtime integrations uninstall codex --repo .
```

For global hooks:

```bash
agent-runtime integrations uninstall codex --global
```

## How It Works

The installer writes Agent Runtime managed entries into:

```text
.codex/hooks.json
```

With `--global`, it writes to:

```text
~/.codex/hooks.json          # macOS / Linux
C:\Users\<you>\.codex\hooks.json   # Windows
```

The hooks cover these Codex hook events:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`

**macOS / Linux hook command** (generated automatically):

```bash
PYTHONPATH=/path/to/packages/sdk-python python3 -m agent_runtime_layer.cli --base-url http://localhost:8000/api codex-hook --event <EVENT_NAME>
```

**Windows hook command** (generated automatically as PowerShell):

```powershell
"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "`$env:PYTHONPATH='...packages\sdk-python'; & 'C:\path\to\python.exe' -m agent_runtime_layer.cli --base-url 'http://localhost:8000/api' codex-hook --event 'SessionStart'"
```

If `agent-runtime` is already on PATH (not a source-checkout), the hook uses the simpler form:

```bash
agent-runtime --base-url http://localhost:8000/api codex-hook --event <EVENT_NAME>
```

It also enables Codex hooks via:

```toml
[features]
hooks = true
```

The hook collector reads Codex hook JSON from stdin, maps it into the Agent Runtime trace schema, and sends events to the local FastAPI backend.

The session fallback reads Codex JSONL records after the run and maps session metadata, prompt, model token usage, tool calls, file changes, terminal output, and task completion into the same trace schema.

## Limitations

- This captures workflow, prompt, tool, file, terminal, and stop evidence exposed by Codex hooks.
- Live hook coverage can vary by Codex CLI version and command mode. Validate with one smoke run after installing hooks.
- Session JSONL fallback is post-run capture, so traces appear after import rather than during the Codex run.
- It does not claim full internal model telemetry unless Codex or provider telemetry exposes it.
- It does not claim real KV-cache hits.
- It does not claim backend or hardware speedup.
- Codex App Server stream support is a future enhancement.
