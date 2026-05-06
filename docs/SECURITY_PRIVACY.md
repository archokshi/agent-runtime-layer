# SECURITY_PRIVACY.md

## Security Philosophy
This product may observe sensitive repo paths, terminal output, prompts, and tool results. The MVP must be local-first and privacy-conscious.

## Required Controls
- Store traces locally by default.
- Provide a config flag to disable raw prompt/body storage.
- Redact obvious secrets before storage.
- Never store `.env` file contents by default.
- Store file paths and metadata by default; raw file content should be opt-in.
- Add a privacy note in README.

## Secret Redaction Patterns
Redact strings matching or containing:
- `sk-` API keys
- `api_key=`
- `password=`
- `token=`
- `secret=`
- AWS access key-like strings
- private key headers

## Data Storage Rules
- Local SQLite by default.
- No outbound telemetry by default.
- Cloud/SaaS is out of MVP scope.

## Tool Execution Rule
The MVP may wrap commands for timing, but it should not autonomously run dangerous commands beyond what the user explicitly passes.
