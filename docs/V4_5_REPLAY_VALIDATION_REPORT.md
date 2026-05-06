# v4.5 Replay Validation + Scenario Expansion Report

Date: 2026-05-04

## Scope

v4.5 expands the Trace Replay Simulator with scenario selection, comparison summaries, confidence explanations, validation evidence requirements, and Markdown export.

This remains a rule-based projection layer. It does not perform real KV-cache control, live backend routing, production scheduling, hardware simulation, RTL, ASIC design, FPGA output, watt-dollar measurement, or measured hardware improvement.

## Implemented

- Selectable replay scenarios
- Five scenario support:
  - persistent prefix cache
  - tool-wait scheduler
  - prefill/decode split
  - warm context tier
  - KV/context compression
- Per-scenario projection confidence reason
- Per-scenario real-backend-validation flag
- Per-scenario validation evidence checklist
- Replay comparison summary:
  - best duration scenario
  - best cost scenario
  - best prefill scenario
- Replay Markdown export
- Dashboard scenario checkboxes
- Dashboard replay comparison cards
- Dashboard Export Replay action

## Validation Completed

- Backend test validates all five scenarios in one replay report.
- Backend test validates comparison summary.
- Backend test validates confidence reason and validation evidence requirements.
- Backend test validates replay Markdown export.
- Frontend production build validates scenario selection UI.

## Remaining Real-World Validation

- Run selected scenarios across 100+ real traces.
- Run at least one measured backend experiment for each high-confidence scenario.
- Compare projected vs measured improvements.
- Calibrate scenario formulas and confidence scores from real measurements.

## Current Claim

Supported:

Agent Runtime Layer v4.5 can replay a blueprint through selected rule-based what-if scenarios and explain what evidence would be needed to validate the projection.

Not supported yet:

Agent Runtime Layer v4.5 has not measured real backend or hardware speedup from those scenarios.
