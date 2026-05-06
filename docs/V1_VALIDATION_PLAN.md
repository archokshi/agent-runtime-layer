# v1.0 Real-World Validation Plan

## Goal

Prove Agent Runtime Layer works on real AI coding-agent workloads and produces measurable optimization value.

This validation layer is scaffolding for real-world evaluation. It does not implement a full SWE-bench runner and does not claim real KV-cache control.

## Validation Track A: SWE-bench Mini-Suite

Run 10-25 tasks from SWE-bench Verified or SWE-bench Lite.

Measure:
- trace completion rate
- model calls per task
- tool calls per task
- repeated context percent
- tool wait percent
- retry loops
- task success or failure
- cost per completed task
- time to completed task

Success Criteria:
- >=80% runs produce complete traces
- >=70% traces produce useful bottleneck diagnosis
- >=50% traces produce actionable optimization recommendation
- at least 5 tasks get before/after optimization comparison

## Validation Track B: Real Coding-Agent Integration

Run at least one real coding agent:
- Aider
- OpenHands
- custom LangGraph coding agent
- CLI wrapper around Claude Code/Codex/Cursor where possible

Measure:
- file events
- terminal events
- model/tool calls
- failed test to retry to fix loops
- dashboard interpretability
- recommendation usefulness

Success Criteria:
- capture full coding-agent loop
- identify top bottleneck
- produce actionable recommendation
- developer can understand trace in under 2 minutes

## Validation Track C: Before/After Repeated-Context Optimization

Run baseline and optimized versions of the same tasks.

Baseline:
Agent sends repeated stable context across model calls.

Optimized:
Agent Runtime Layer detects stable context blocks and recommends removing, separating, or restructuring repeated context.

Measure:
- repeated input tokens
- estimated prefill cost
- total model cost
- task latency
- task success rate

Success Criteria:
- 25-40% reduction in repeated input tokens
- 15-30% estimated cost reduction
- no degradation in task success rate
- recommendation evidence visible in dashboard

## Validation Track D: Blueprint Quality Review

For each optimized task, generate an Agent Silicon Blueprint Preview.

Human review should answer:
- Is the recommendation supported by trace evidence?
- Is the hardware/system implication reasonable?
- Is confidence level calibrated?
- Is the next validation step clear?

Success Criteria:
- >=80% Blueprint recommendations judged reasonable by reviewer
- no unsupported hardware claims
- all recommendations include evidence, implication, confidence, and next step

## Implemented v1.0 Validation Scaffolding

Data model metadata:
- `benchmark_name`
- `benchmark_task_id`
- `repo_name`
- `issue_id`
- `agent_name`
- `baseline_or_optimized`
- `task_success`
- `tests_passed`
- `tests_failed`
- `patch_generated`
- `files_changed_count`
- `retry_count`
- `before_after_pair_id`

Dashboard support:
- validation summary section
- task outcome metadata
- patch/test metadata
- before/after comparison table
- repeated-context reduction
- estimated cost reduction
- task success preservation

Analyzer support:
- repeated input token reduction percent
- estimated cost reduction percent
- latency change percent
- success preserved boolean

Sample traces:
- `examples/sample-traces/swebench-style-baseline.json`
- `examples/sample-traces/swebench-style-optimized.json`
- `examples/sample-traces/aider-style-retry-loop.json`

## Current Non-Goals

Do not build yet:
- full SWE-bench runner
- real KV-cache manager
- vLLM/SGLang/Dynamo integration
- hardware simulation
- automatic benchmark orchestration

The v1.0 claim is limited to trace-based validation and measured optimization opportunity.
