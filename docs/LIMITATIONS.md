# Limitations

Agent Runtime Layer is currently a developer preview.

## What It Does

- imports and captures coding-agent traces
- stores traces locally
- analyzes latency, model/tool split, retries, context repetition, and cost estimates
- generates optimization recommendations
- creates prefix-cache-ready context packages
- tracks benchmark evidence records
- generates Workload Reports from local evidence

## What It Does Not Do Yet

- no hosted SaaS
- no production authentication
- no billing system
- no official SWE-bench runner
- no real KV-cache control
- no direct vLLM, SGLang, Dynamo, or LMCache integration
- no production scheduler
- no live GPU polling
- no hardware simulation
- no RTL, FPGA, ASIC, or chip design output

## Estimated vs Measured

Many metrics are estimates derived from trace metadata:

- estimated model cost
- repeated-context opportunity
- projected token reduction
- projected prefill reduction

Measured claims require imported measured validation records or backend telemetry.

## Privacy

Traces may contain sensitive information. Redaction is best-effort. Review traces before sharing them publicly.

