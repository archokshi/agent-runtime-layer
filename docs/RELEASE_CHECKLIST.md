# Release Checklist

Use this before publishing or tagging a release.

## Repository Hygiene

- [ ] `LICENSE` exists
- [ ] `.env.example` exists
- [ ] `.gitignore` excludes secrets, databases, cache files, and local traces
- [ ] `CONTRIBUTING.md` exists
- [ ] `SECURITY.md` exists
- [ ] `CODE_OF_CONDUCT.md` exists
- [ ] GitHub issue templates exist
- [ ] Pull request template exists
- [ ] GitHub Actions CI exists

## Validation

- [ ] Backend tests pass
- [ ] Frontend production build passes
- [ ] Docker Compose rebuild passes
- [ ] Backend health returns `{"status":"ok"}`
- [ ] Homepage loads
- [ ] Golden demo imports and opens task detail page
- [ ] Workload Report renders after demo

## Public Claim Safety

- [ ] Estimated savings are labeled as estimates
- [ ] Measured claims cite measured validation data
- [ ] No copy claims real KV-cache control
- [ ] No copy claims production scheduler behavior
- [ ] No copy claims hardware simulation or measured hardware speedup
- [ ] No secrets or private traces are included

## Suggested Smoke Commands

```bash
docker compose up --build -d
curl http://localhost:8000/api/health
```

Then open:

```text
http://localhost:3000
```

Click **Start demo** and confirm the task page opens.

