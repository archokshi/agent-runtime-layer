# Cursor Agent Capture

Agent Runtime Layer can capture Cursor Agent runs from Cursor CLI `stream-json` output.

This integration is part of Phase 1.6C: Cursor Agent Capture. It collects real coding-agent evidence for the Phase 1.6 Evidence Campaign and Phase 2 handoff package.

## What It Captures

- Cursor system/session metadata
- user prompt
- assistant/tool stream structure
- tool-call start and end
- file-change evidence from write tool calls
- final result and duration metadata

## Quickstart

Start Agent Runtime Layer:

```bash
docker compose up --build
```

Install the local capture helper:

```bash
agent-runtime integrations install cursor --repo .
```

Run Cursor Agent through the stream capture command:

```bash
cursor-agent --print --output-format stream-json | agent-runtime cursor-stream --repo .
```

Open the dashboard:

```text
http://localhost:3000
```

Each captured Cursor Agent run should appear as a task trace.

## Status

```bash
agent-runtime integrations status cursor --repo .
```

## Uninstall

```bash
agent-runtime integrations uninstall cursor --repo .
```

## Limitations

- This uses Cursor Agent CLI stream output first, not private Cursor IDE internals.
- Cursor Background Agents API import is a future extension.
- It does not claim full internal model telemetry unless Cursor or provider telemetry exposes it.
- It does not claim real KV-cache hits.
- It does not claim backend or hardware speedup.
