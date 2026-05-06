# Contributing

Thanks for helping improve Agent Runtime Layer.

By contributing, you agree that your contributions are licensed under the same license as the project: AGPL-3.0-or-later.

## Development Setup

Run the app locally:

```bash
docker compose up --build
```

Open:

- Dashboard: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Golden Demo

After the app starts, click **Start demo** on the homepage. The demo imports a bundled coding-agent trace, generates analysis artifacts, and opens the task detail page.

## Local Validation

Backend tests:

```bash
cd backend
PYTHONPATH=. python -m pytest tests
```

Frontend build:

```bash
cd frontend
npm ci
npm run build
```

Docker smoke test:

```bash
docker compose up --build -d
curl http://localhost:8000/api/health
```

## Pull Request Guidelines

- Keep changes focused.
- Add or update tests for behavior changes.
- Update docs when user-facing behavior changes.
- Do not commit `.env`, SQLite databases, cache folders, local traces, or generated test artifacts.
- Avoid overclaiming optimization results. Label estimates as estimates unless they are backed by measured validation data.

## Product Boundaries

Agent Runtime Layer currently provides trace profiling, deterministic analysis, optimization recommendations, and local evidence reports. It does not claim real KV-cache control, production scheduler behavior, hardware simulation, or measured hardware speedups.
