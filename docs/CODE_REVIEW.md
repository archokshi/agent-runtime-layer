# CODE_REVIEW.md

Use this checklist for Codex review.

## Correctness
- Does the trace schema match docs/TRACE_SCHEMA.md?
- Are API responses stable and documented?
- Does the analyzer produce deterministic outputs?
- Can multiple traces/tasks be imported?

## UX
- Can a user run the product from README alone?
- Does the dashboard show useful insight with sample traces?
- Are bottleneck labels understandable?
- Does the Silicon Blueprint preview avoid unsupported claims?

## Security
- Are obvious secrets redacted?
- Is raw code/prompt storage optional where possible?
- Does local-first mode avoid outbound telemetry?

## Tests
- Are ingestion tests included?
- Are analyzer tests included?
- Are sample traces covered?
- Does Docker startup work?

## Scope Control
- No full hardware simulator in MVP.
- No real KV-cache control in MVP.
- No production auth unless required for basic app bootstrapping.
