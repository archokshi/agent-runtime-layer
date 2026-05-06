# Agent Runtime Layer Demo

## v0.1 Sample Trace Demo

```bash
docker compose up --build -d
curl -X POST http://localhost:8000/api/traces/import \
  -H "Content-Type: application/json" \
  --data-binary @examples/sample-traces/repeated-context-task.json
```

Open `http://localhost:3000/tasks/task_repeated_context_001`.

## v0.2 Real Local Trace Capture Demo

Generate a local trace JSON:

```bash
cd packages/sdk-python
python -m agent_runtime_layer.cli trace --name "hello test" -- python -c "print('hello')"
```

Import the generated trace:

```bash
python -m agent_runtime_layer.cli import .agent-runtime/traces/<task_id>.json
```

Or generate and upload in one step:

```bash
python -m agent_runtime_layer.cli trace --name "hello test" --upload -- python -c "print('hello')"
```

Then open the generated task in the dashboard.

## v0.3 SDK Model/Tool Instrumentation Demo

Generate a custom-agent SDK trace:

```bash
cd packages/sdk-python
python examples/custom_agent_demo.py
```

Import the generated trace:

```bash
python -m agent_runtime_layer.cli import .agent-runtime/traces/<task_id>.json
```

Open the task dashboard. It should show model calls, tool calls, token flow, repeated context, and Silicon Blueprint preview recommendations from SDK-generated events.

## v0.4 Aider Integration Demo

The real integration wraps an Aider CLI command:

```bash
cd packages/sdk-python
python -m agent_runtime_layer.cli integrate aider \
  --name "aider fix task" \
  --repo path/to/repo \
  --upload \
  -- aider path/to/file.py --message "Make the requested change"
```

For local validation without Aider credentials, use the mock demo in `docs/AIDER_INTEGRATION.md`.
