#!/usr/bin/env bash
# Agentium — Automated QA Suite
# Usage: bash scripts/qa-run.sh
# Tears down, installs fresh via curl, runs 10 Claude Code prompts,
# checks every metric, prints a full pass/fail report.

set -e

API="http://localhost:8000/api"
PASS=0; FAIL=0
RESULTS=()

ok()   { PASS=$((PASS+1)); RESULTS+=("  ✅  $1"); }
fail() { FAIL=$((FAIL+1)); RESULTS+=("  ❌  $1"); }
step() { echo ""; echo ">> $1"; }

# ── Python detection (handles Windows Store shim) ─────────────
find_python() {
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      ver=$("$cmd" --version 2>&1)
      if [[ "$ver" == Python\ 3* ]]; then echo "$cmd"; return; fi
    fi
  done
  for p in \
    "/c/Python313/python.exe" "/c/Python312/python.exe" \
    "/c/Python311/python.exe" "/c/Python310/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python313/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python312/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe"; do
    if [[ -x "$p" ]] && [[ "$("$p" --version 2>&1)" == Python\ 3* ]]; then
      echo "$p"; return
    fi
  done
  echo ""
}

PY=$(find_python)

echo ""
echo "==========================================="
echo "  Agentium Automated QA Suite"
echo "==========================================="

# ── 1. Uninstall cleanly ──────────────────────────────────────
step "1. Uninstalling previous install..."
INSTALL_DIR="$HOME/.agentium"
if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
  cd "$INSTALL_DIR"
  docker compose down -v 2>/dev/null || true
  cd - > /dev/null
fi
rm -rf "$INSTALL_DIR"
if [[ -n "$PY" ]]; then
  "$PY" -m pip uninstall agentium-tracer -y 2>/dev/null || true
fi
echo "  Clean."

# ── 2. Fresh install ─────────────────────────────────────────
step "2. Running installer..."
curl -sSL https://agent-runtime-layer.vercel.app/install.sh | bash
echo "  Installer done."

# ── 3. Check SDK version ─────────────────────────────────────
step "3. Checking SDK..."
PY=$(find_python)  # re-detect after install may have added Python
if [[ -z "$PY" ]]; then
  fail "Python not found — cannot verify SDK"
else
  SDK_VER=$("$PY" -m pip show agentium-tracer 2>/dev/null | grep "^Version:" | awk '{print $2}')
  if [[ -n "$SDK_VER" ]]; then
    ok "SDK installed: agentium-tracer $SDK_VER"
  else
    fail "SDK not installed"
  fi
fi

# ── 4. Check global hooks ────────────────────────────────────
step "4. Checking global hooks..."
HOOKS_FILE="$HOME/.claude/settings.json"
if [[ -f "$HOOKS_FILE" ]] && grep -q "agentium_integration" "$HOOKS_FILE" 2>/dev/null; then
  ok "Claude Code hooks installed globally (~/.claude/settings.json)"
else
  fail "Claude Code global hooks not found"
fi

CODEX_HOOKS="$HOME/.codex/hooks.json"
if [[ -f "$CODEX_HOOKS" ]] && grep -q "agentium_integration" "$CODEX_HOOKS" 2>/dev/null; then
  ok "Codex hooks installed globally (~/.codex/hooks.json)"
else
  fail "Codex global hooks not found"
fi

# ── 5. Backend health ────────────────────────────────────────
step "5. Checking backend..."
sleep 5
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API/health")
if [[ "$HEALTH" == "200" ]]; then
  ok "Backend healthy (port 8000)"
else
  fail "Backend not responding (HTTP $HEALTH)"
fi

DASH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:4001/runs")
if [[ "$DASH" == "200" ]]; then
  ok "Dashboard reachable (port 4001)"
else
  fail "Dashboard not responding (HTTP $DASH)"
fi

# ── 6. Run 10 Claude Code prompts ───────────────────────────
step "6. Running 10 Claude Code prompts..."

PROMPTS=(
  "What is 2+2? Answer in one word."
  "List 3 programming languages in a comma-separated list."
  "What color is the sky? One word."
  "Create a file called qa-test-1.txt with the word 'hello' in it."
  "Read the file qa-test-1.txt and tell me its contents."
  "What is the capital of France? One word."
  "Run a bash command: echo 'qa-test' and show me the output."
  "Create a file called qa-test-2.txt with today's date in it."
  "List the files in the current directory."
  "Delete the files qa-test-1.txt and qa-test-2.txt."
)

RAN=0
for prompt in "${PROMPTS[@]}"; do
  result=$(claude --print "$prompt" 2>/dev/null && echo "ok" || echo "fail")
  if [[ "$result" != "fail" ]]; then
    RAN=$((RAN+1))
  fi
  sleep 2
done
echo "  Ran $RAN/10 prompts."

if [[ $RAN -ge 10 ]]; then
  ok "All 10 prompts executed"
elif [[ $RAN -ge 8 ]]; then
  ok "$RAN/10 prompts executed (acceptable)"
else
  fail "Only $RAN/10 prompts ran"
fi

# ── 7. Check traces in backend ───────────────────────────────
step "7. Checking traces..."
sleep 10  # give hooks time to flush

TASKS_JSON=$(curl -s "$API/tasks")
TASK_COUNT=$(echo "$TASKS_JSON" | "$PY" -c "import sys,json; t=json.load(sys.stdin); print(len(t))" 2>/dev/null || echo "0")

if [[ "$TASK_COUNT" -ge 10 ]]; then
  ok "$TASK_COUNT runs traced (≥10 expected)"
else
  fail "Only $TASK_COUNT runs traced (expected ≥10)"
fi

# ── 8. Check metrics via analysis endpoint ───────────────────
step "8. Checking metrics (cost, model calls, CTX%)..."

# Get the 5 most recent completed tasks
RECENT_IDS=$(echo "$TASKS_JSON" | "$PY" -c "
import sys, json
tasks = json.load(sys.stdin)
completed = [t['task_id'] for t in tasks if t.get('status') == 'completed'][-5:]
print(' '.join(completed))
" 2>/dev/null)

COST_COUNT=0
CALLS_COUNT=0
CTX_COUNT=0
TOTAL_CHECKED=0

for task_id in $RECENT_IDS; do
  ANALYSIS=$(curl -s "$API/tasks/$task_id/analysis" 2>/dev/null)
  if [[ -z "$ANALYSIS" ]]; then continue; fi
  TOTAL_CHECKED=$((TOTAL_CHECKED+1))

  COST=$(echo "$ANALYSIS" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('estimated_total_cost_dollars',0))" 2>/dev/null || echo "0")
  CALLS=$(echo "$ANALYSIS" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('model_call_count',0))" 2>/dev/null || echo "0")
  CTX=$(echo "$ANALYSIS" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('repeated_context_percent',0))" 2>/dev/null || echo "0")

  if "$PY" -c "import sys; sys.exit(0 if float('$COST') > 0 else 1)" 2>/dev/null; then COST_COUNT=$((COST_COUNT+1)); fi
  if "$PY" -c "import sys; sys.exit(0 if int('$CALLS') > 0 else 1)" 2>/dev/null; then CALLS_COUNT=$((CALLS_COUNT+1)); fi
  if "$PY" -c "import sys; sys.exit(0 if float('$CTX') > 0 else 1)" 2>/dev/null; then CTX_COUNT=$((CTX_COUNT+1)); fi
done

if [[ $COST_COUNT -ge 3 ]]; then
  ok "Cost populating ($COST_COUNT/$TOTAL_CHECKED recent runs have real cost)"
else
  fail "Cost not populating ($COST_COUNT/$TOTAL_CHECKED runs)"
fi

if [[ $CALLS_COUNT -ge 3 ]]; then
  ok "Model calls populating ($CALLS_COUNT/$TOTAL_CHECKED recent runs)"
else
  fail "Model calls not populating ($CALLS_COUNT/$TOTAL_CHECKED runs)"
fi

if [[ $CTX_COUNT -ge 3 ]]; then
  ok "Repeated CTX% populating ($CTX_COUNT/$TOTAL_CHECKED recent runs)"
else
  fail "Repeated CTX% not populating ($CTX_COUNT/$TOTAL_CHECKED runs)"
fi

# ── 9. Run detail page ───────────────────────────────────────
step "9. Checking run detail page..."
FIRST_ID=$(echo "$TASKS_JSON" | "$PY" -c "
import sys,json; t=json.load(sys.stdin)
c=[x for x in t if x.get('status')=='completed']
print(c[-1]['task_id'] if c else '')
" 2>/dev/null)

if [[ -n "$FIRST_ID" ]]; then
  DETAIL=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:4001/runs/$FIRST_ID")
  if [[ "$DETAIL" == "200" ]]; then
    ok "Run detail page loads (/runs/$FIRST_ID)"
  else
    fail "Run detail page failed (HTTP $DETAIL)"
  fi
else
  fail "No completed task to test run detail page"
fi

# ── Summary ──────────────────────────────────────────────────
TOTAL=$((PASS+FAIL))
echo ""
echo "==========================================="
echo "  QA Results: $PASS/$TOTAL passed"
echo "==========================================="
for r in "${RESULTS[@]}"; do echo "$r"; done
echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "  🎉  ALL CHECKS PASSED — ready to ship"
elif [[ $FAIL -le 2 ]]; then
  echo "  ⚠️   $FAIL minor issue(s) — review above"
else
  echo "  ❌  $FAIL failures — fix before shipping"
fi
echo "==========================================="
echo ""
