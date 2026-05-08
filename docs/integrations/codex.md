# Codex Native Capture

Agent Runtime Layer can capture Codex coding-agent runs through Codex hooks.

This integration is part of Phase 1.6A: Codex Native Capture. It is designed to collect real coding-agent evidence for the Phase 1.6 Evidence Campaign and Phase 2 handoff package.

## What It Captures

- Codex session metadata
- user prompt / turn start
- tool-call start and end
- terminal command evidence when exposed by the hook payload
- file-change evidence when exposed by the hook payload
- task end / stop event
- post-run Codex session JSONL when live hooks are unavailable

## Quickstart

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

Run Codex normally in that repository.

Open the dashboard:

```text
http://localhost:3000
```

Each captured Codex turn should appear as a task trace.

## Reliable Fallback: Import Codex Session JSONL

Some Codex CLI modes may not fire hooks on every platform. If a real Codex run completes but no task appears in the dashboard, import the Codex session JSONL after the run:

```bash
agent-runtime codex-session ~/.codex/sessions/YYYY/MM/DD/rollout-....jsonl --project codex-live --upload
```

On Windows, the session files are usually under:

```text
C:\Users\<you>\.codex\sessions\YYYY\MM\DD\
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
~/.codex/hooks.json
```

If `--global` is run from an Agent Runtime Layer source checkout, the hook command uses the checkout's Python SDK directly. That makes live validation work before `agent-runtime` is installed globally on `PATH`.

It also enables Codex hooks with:

```toml
[features]
hooks = true
```

Older Codex builds referenced `codex_hooks`; current Codex CLI reports that key as deprecated and uses `hooks`.

The hooks call:

```bash
agent-runtime codex-hook --event <EVENT_NAME>
```

For source-checkout global installs, the generated command is equivalent to:

```bash
python -m agent_runtime_layer.cli codex-hook --event <EVENT_NAME>
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
