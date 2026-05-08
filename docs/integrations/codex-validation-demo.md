# Codex Validation Demo

This demo validates the reliable Codex post-run capture path.

## Goal

Run a real Codex task, import the completed Codex session JSONL, and inspect the trace in Agent Runtime Layer.

## 1. Start Agent Runtime Layer

```bash
docker compose up --build
```

Open:

```text
http://localhost:3000
```

## 2. Run A Small Codex Task

From a small test repository, run Codex and ask it to make a small file change, then verify it.

Example task:

```text
Create hello-codex.txt with exactly one line: hello from codex validation
```

## 3. Find The Codex Session JSONL

Codex sessions are usually stored under:

```text
C:\Users\<you>\.codex\sessions\YYYY\MM\DD\
```

Pick the latest `rollout-....jsonl` for the run you just completed.

## 4. Import The Session

```bash
agent-runtime codex-session C:\Users\<you>\.codex\sessions\YYYY\MM\DD\rollout-....jsonl --project codex-live --upload
```

If you are running from the source checkout before installing the package globally:

```bash
$env:PYTHONPATH="packages/sdk-python"
python -m agent_runtime_layer.cli codex-session C:\Users\<you>\.codex\sessions\YYYY\MM\DD\rollout-....jsonl --project codex-live --upload
```

## 5. Inspect The Dashboard

Open the imported task. You should see:

- `Source: Codex session JSONL`
- task start/end
- prompt context snapshot
- model call token usage when present in the Codex session
- tool calls
- file changes
- terminal output
- task success metadata

## What This Proves

This proves Agent Runtime Layer can ingest a real completed Codex coding-agent run and turn it into a dashboard trace.

## What This Does Not Claim

- It is post-run capture, not live streaming.
- It does not claim private model internals.
- It does not claim real KV-cache hits.
- It does not claim backend or hardware speedup.
