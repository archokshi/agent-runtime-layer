# Aider Integration

Agent Runtime Layer v0.4 adds a first coding-agent integration adapter for Aider.

The adapter wraps an Aider CLI command and maps the run into the Agent Runtime trace schema:

- `task_start`
- `tool_call_start` for the Aider CLI run
- `terminal_event` for stdout/stderr and duration
- `model_call_start` and `model_call_end` when Aider prints model/token/cost metadata
- `file_event` for Git working tree changes
- `tool_call_end`
- `task_end`

The model-call events are synthetic adapter events parsed from Aider stdout. They include model name, input tokens, output tokens, and message cost when Aider emits lines such as `Model: ...` and `Tokens: ... Cost: ...`.

## Real Aider Run

Install and configure Aider separately, including any model provider credentials it needs. Then run:

```bash
cd packages/sdk-python
python -m agent_runtime_layer.cli integrate aider \
  --name "aider fix task" \
  --repo path/to/repo \
  --upload \
  -- aider path/to/file.py --message "Make the requested change"
```

If `--upload` is omitted, the trace is written locally to `.agent-runtime/traces/<task_id>.json`.

## Local Mock Demo

This repository includes a mock Aider-like command for validating the adapter without provider credentials:

```bash
cd packages/sdk-python/examples/aider-demo-repo
git init
git add app.py
git -c user.email=test@example.com -c user.name=Test commit -m init
cd ../..
python -m agent_runtime_layer.cli integrate aider \
  --name "mock aider demo" \
  --repo examples/aider-demo-repo \
  --upload \
  -- python ../mock_aider_edit.py
```

Open the generated task in the dashboard. It should show terminal activity, file metadata, a tool-wait bottleneck, and Silicon Blueprint preview output where supported by metrics.

## Limitations

- The adapter does not hook into Aider internals yet; model-call details are parsed from Aider output.
- Model-call details depend on what Aider exposes or logs.
- No closed-source coding-agent hooks are used.
- No real KV-cache control or hardware simulation is included.
