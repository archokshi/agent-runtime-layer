# Quickstart

This guide gets Agent Runtime Layer running with the golden demo.

## Requirements

- Docker Desktop
- Git

Node and Python are only required if you want to run the frontend/backend outside Docker.

## Start

```bash
docker compose up --build
```

Open:

```text
http://localhost:3000
```

## Run the Golden Demo

Click **Start demo**.

The app imports a bundled coding-agent trace, generates the analysis artifacts, and opens the task page.

The demo shows:

- failed test -> repair -> passing test loop
- model calls
- terminal/tool calls
- file edit event
- repeated context
- estimated model cost
- bottleneck diagnosis
- optimization recommendations
- prefix-cache-ready context package
- Workload Report

## Verify the Backend

```bash
curl http://localhost:8000/api/health
```

Expected:

```json
{"status":"ok"}
```

## Import a Sample Trace Manually

```bash
curl -X POST http://localhost:8000/api/traces/import \
  -H "Content-Type: application/json" \
  --data-binary @examples/sample-traces/repeated-context-task.json
```

Then open the task from the dashboard.

