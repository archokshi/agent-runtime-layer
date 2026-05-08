# Claude Code Native Capture

Agent Runtime Layer can capture Claude Code coding-agent runs through Claude Code hooks.

This integration is part of Phase 1.6B: Claude Code Native Capture. It collects real coding-agent evidence for the Phase 1.6 Evidence Campaign and Phase 2 handoff package.

## What It Captures

- Claude Code session metadata
- user prompt / turn start
- tool-call start and end
- tool failure events
- terminal command evidence from Bash hooks
- file-change evidence from Edit/Write hooks
- task end / stop event

## Quickstart

Start Agent Runtime Layer:

```bash
docker compose up --build
```

Install repo-local Claude Code hooks inside the repository where you run Claude Code:

```bash
agent-runtime integrations install claude-code --repo .
```

Run Claude Code normally in that repository.

Open the dashboard:

```text
http://localhost:3000
```

Each captured Claude Code turn should appear as a task trace.

## Status

```bash
agent-runtime integrations status claude-code --repo .
```

## Uninstall

```bash
agent-runtime integrations uninstall claude-code --repo .
```

## Limitations

- This captures workflow, prompt, tool, file, terminal, failure, and stop evidence exposed by Claude Code hooks.
- It does not claim full internal model telemetry unless Claude Code or provider telemetry exposes it.
- It does not claim real KV-cache hits.
- It does not claim backend or hardware speedup.
