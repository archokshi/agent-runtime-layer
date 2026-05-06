# PROJECT_STRUCTURE.md

Recommended repository structure:

```text
agent-runtime-layer/
  AGENTS.md
  README.md
  docker-compose.yml
  backend/
    app/
      main.py
      models.py
      db.py
      routes/
      analyzer/
      security/
    tests/
    pyproject.toml
  frontend/
    app/
    components/
    lib/
    package.json
  packages/
    sdk-python/
      agent_runtime/
      tests/
      pyproject.toml
  examples/
    sample-traces/
      successful-coding-task.json
      tool-heavy-task.json
      repeated-context-task.json
  docs/
    BUILD_PLAN.md
    ACCEPTANCE_TESTS.md
    TRACE_SCHEMA.md
    API_SPEC.md
    SECURITY_PRIVACY.md
    CODE_REVIEW.md
```
