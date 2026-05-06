# v1.5 Optimization Executor

v1.5 turns repeated-context recommendations into an executable artifact.

It does not control a real KV cache. It creates a prefix-cache-ready prompt/context package and estimates the token, cost, and prefill opportunity that a compatible backend could exploit later.

## Scope

- Detect stable repeated context blocks.
- Separate dynamic task context from stable context.
- Generate stable prefix references and dynamic payload references.
- Persist a context optimization report.
- Show before/after estimated token and cost savings in the dashboard.

## Main Endpoint

```bash
curl -X POST http://localhost:8000/api/tasks/<task_id>/optimize-context
```

The persisted report can be fetched with:

```bash
curl http://localhost:8000/api/tasks/<task_id>/optimized-context
```

## Controlled Demo

Import the controlled repeated-context sample:

```bash
cd packages/sdk-python
python -m agent_runtime_layer.cli import ../../examples/sample-traces/v1_5_repeated_context_baseline.json
```

Open `task_v1_5_repeated_context_baseline`, then click **Run Optimize Context**.

Expected result:

- Stable context blocks are detected.
- Dynamic context blocks remain in the task payload.
- The optimized package references stable prefix blocks.
- The controlled sample shows roughly 30% estimated input token, cost, and prefill reduction.

## Real Model-Call Validation

For a small real OpenAI before/after experiment, run:

```bash
python examples/v1_5_controlled_openai_experiment.py
```

The script:

- makes real model calls using `OPENAI_API_KEY`
- creates a baseline trace that repeats stable context across calls
- creates an optimized trace that sends stable context once and uses a stable prefix reference on the second call
- imports both traces into the local backend if it is running
- prints task IDs, model usage tokens, estimated cost, and before/after reduction

This proves real model-token measurement for the context-packaging idea. It still does not claim actual KV-cache hits.

Latest local validation run:

- Baseline task: `task_v1_5_real_context_baseline_203c3d6d`
- Optimized task: `task_v1_5_real_context_optimized_203c3d6d`
- Pair id: `pair_v1_5_real_context_203c3d6d`
- Model: `gpt-4o-mini`
- Measured input tokens: 424 baseline to 281 optimized
- Measured input-token reduction: 33.73%
- Estimated cost reduction from paired traces: 10.67%
- Baseline optimizer report: 30.9% estimated input-token, cost, and prefill reduction
- Success preserved: true

## Non-Goals

- No real KV-cache control.
- No vLLM, SGLang, or Dynamo integration.
- No runtime scheduler.
- No backend-aware routing.
- No hardware simulation.
