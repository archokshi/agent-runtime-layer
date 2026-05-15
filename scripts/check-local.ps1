# Agentium — Local Verification Script
# Usage: .\scripts\check-local.ps1
# Run from the repo root before every demo or release.

$pass = 0
$fail = 0

function Ok($msg)  { Write-Host "  [PASS] $msg" -ForegroundColor Green;  $script:pass++ }
function Err($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:fail++ }
function Step($msg){ Write-Host "`n>> $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "==========================================" -ForegroundColor White
Write-Host "  Agentium — Local Verification Check     " -ForegroundColor White
Write-Host "==========================================" -ForegroundColor White

# ── 1. Docker health ─────────────────────────────────────────────────────
Step "1. Docker services"

$health = docker inspect --format='{{.State.Health.Status}}' agent-runtime-layer-backend-1 2>$null
if ($health -eq "healthy") { Ok "Backend container healthy" }
else { Err "Backend container not healthy (status: $health) — run: docker compose up -d" }

$dashV3 = docker inspect --format='{{.State.Status}}' agent-runtime-layer-customer-dashboard-v3-1 2>$null
if ($dashV3 -eq "running") { Ok "customer-dashboard-v3 container running" }
else { Err "customer-dashboard-v3 not running (status: $dashV3)" }

# ── 2. API health ─────────────────────────────────────────────────────────
Step "2. API endpoints"

$routes = @(
    @{ url = "http://localhost:8000/api/health";           label = "GET /api/health" }
    @{ url = "http://localhost:8000/api/tasks";            label = "GET /api/tasks" }
    @{ url = "http://localhost:8000/api/settings";         label = "GET /api/settings" }
    @{ url = "http://localhost:8000/api/budget/summary";   label = "GET /api/budget/summary" }
    @{ url = "http://localhost:8000/api/optimization-proofs"; label = "GET /api/optimization-proofs" }
    @{ url = "http://localhost:8000/api/context-memory/summary"; label = "GET /api/context-memory/summary" }
)

foreach ($r in $routes) {
    try {
        $res = Invoke-WebRequest -Uri $r.url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($res.StatusCode -eq 200) { Ok $r.label }
        else { Err "$($r.label) returned $($res.StatusCode)" }
    } catch {
        Err "$($r.label) — $($_.Exception.Message)"
    }
}

# ── 3. Dashboard routes ───────────────────────────────────────────────────
Step "3. Dashboard routes (port 4001 — canonical)"

$dashRoutes = @(
    "/overview", "/runs", "/settings", "/bottlenecks", "/context", "/cost", "/recommendations"
)

foreach ($route in $dashRoutes) {
    try {
        $res = Invoke-WebRequest -Uri "http://localhost:4001$route" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($res.StatusCode -in @(200, 307)) { Ok "GET localhost:4001$route" }
        else { Err "localhost:4001$route returned $($res.StatusCode)" }
    } catch {
        Err "localhost:4001$route — $($_.Exception.Message)"
    }
}

# ── 4. Settings API smoke test ────────────────────────────────────────────
Step "4. Settings API — plan gate check"

try {
    $settings = Invoke-RestMethod -Uri "http://localhost:8000/api/settings" -Method GET -TimeoutSec 5
    if ($null -ne $settings.plan) { Ok "Settings returns plan=$($settings.plan)" }
    else { Err "Settings response missing 'plan' field" }

    # Test that free plan blocks optimizer_enabled
    $blocked = $false
    try {
        Invoke-RestMethod -Uri "http://localhost:8000/api/settings" -Method PATCH `
            -ContentType "application/json" `
            -Body '{"plan":"free","optimizer_enabled":true}' `
            -TimeoutSec 5 | Out-Null
    } catch {
        if ($_.Exception.Response.StatusCode -eq 403) {
            $blocked = $true
        }
    }
    if ($blocked) { Ok "Plan gate blocks optimizer on free plan (403 returned)" }
    else { Err "Plan gate did NOT block optimizer on free plan — check PLAN_GATES" }
} catch {
    Err "Settings smoke test failed: $($_.Exception.Message)"
}

# ── 5. Docker images on Hub ───────────────────────────────────────────────
Step "5. Docker Hub images"

$images = @("archokshi/backend:latest", "archokshi/dashboard:latest")
foreach ($img in $images) {
    $exists = docker image inspect $img 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "Local image: $img" }
    else { Err "Local image not found: $img — run: docker pull $img" }
}

# ── 6. Install script reachable ───────────────────────────────────────────
Step "6. Install page (Vercel)"

try {
    $res = Invoke-WebRequest -Uri "https://agent-runtime-layer.vercel.app" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($res.StatusCode -eq 200) { Ok "Install page live: agent-runtime-layer.vercel.app" }
    else { Err "Install page returned $($res.StatusCode)" }
} catch {
    Err "Install page unreachable: $($_.Exception.Message)"
}

# ── Summary ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor White
if ($fail -eq 0) {
    Write-Host "  ALL $pass CHECKS PASSED — ready to demo " -ForegroundColor Green
} else {
    Write-Host "  $pass passed · $fail FAILED — fix before demo " -ForegroundColor Red
}
Write-Host "==========================================" -ForegroundColor White
Write-Host ""
