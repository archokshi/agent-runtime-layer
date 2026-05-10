# Claude Code Native Capture

Agent Runtime Layer can capture Claude Code coding-agent runs through Claude Code hooks.

This integration is part of Phase 1.6B: Claude Code Native Capture. It collects real coding-agent evidence for the Phase 1.6 Evidence Campaign and Phase 2 handoff package.

## Prerequisites

- Docker Desktop running (backend on port 8000, dashboards on ports 3000 and 4000)
- Python 3.10+
- [Claude Code](https://claude.ai/code) installed
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

- Claude Code session metadata
- user prompt / turn start
- tool-call start and end
- tool failure events
- terminal command evidence from Bash hooks
- file-change evidence from Edit/Write hooks
- task end / stop event

## Quickstart

### macOS / Linux

Start Agent Runtime Layer:

```bash
docker compose up --build
```

Install repo-local Claude Code hooks inside the repository where you run Claude Code:

```bash
agent-runtime integrations install claude-code --repo .
```

Run Claude Code normally in that repository. Open the customer dashboard:

```text
http://localhost:4000
```

Each captured Claude Code turn appears as a task trace. The developer dashboard (with full analysis) is at:

```text
http://localhost:3000
```

### Windows

Start Agent Runtime Layer (PowerShell):

```powershell
docker compose up --build
```

Install Claude Code hooks:

```powershell
agent-runtime integrations install claude-code --repo .
```

Run Claude Code normally. Open the dashboard:

```text
http://localhost:4000
```

## Status

```bash
agent-runtime integrations status claude-code --repo .
```

## Uninstall

```bash
agent-runtime integrations uninstall claude-code --repo .
```

## How It Works

The installer writes Agent Runtime managed hook entries into:

```text
.claude/settings.local.json
```

The hooks cover all 7 Claude Code hook events:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PostToolUseFailure`
- `Stop`
- `SessionEnd`

Each hook calls:

```bash
agent-runtime --base-url http://localhost:8000/api claude-hook --event <EVENT_NAME>
```

The hook collector reads the Claude Code hook JSON payload from stdin, maps it into the Agent Runtime trace schema, and sends events to the local FastAPI backend at `http://localhost:8000/api`.

One task trace is created per Claude Code turn (each `UserPromptSubmit`). Tool calls, file changes, terminal commands, and failures are all captured as child events within that trace.

## Limitations

- This captures workflow, prompt, tool, file, terminal, failure, and stop evidence exposed by Claude Code hooks.
- It does not claim full internal model telemetry unless Claude Code or provider telemetry exposes it.
- It does not claim real KV-cache hits.
- It does not claim backend or hardware speedup.
