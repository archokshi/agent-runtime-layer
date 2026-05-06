# Security Policy

Agent Runtime Layer is designed to run as a self-hosted developer tool. Traces can contain sensitive prompts, file paths, terminal output, tool results, and project metadata.

## Reporting Security Issues

Please do not open a public issue for a suspected vulnerability.

For now, report privately to the repository owner. Once the project has a public security contact, this file should be updated with the preferred email or GitHub Security Advisory process.

## Data Handling

- The app stores data locally in SQLite by default.
- No outbound product telemetry is sent by default.
- Obvious secrets are redacted before persistence where possible.
- Users should avoid importing full file contents, raw `.env` content, private keys, or unredacted production logs.

## Non-Goals

This project does not currently provide production authentication, multi-tenant isolation, hosted SaaS security controls, or enterprise access management.

