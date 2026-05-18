# Agentium Installer for Windows (PowerShell)
# Run: Set-ExecutionPolicy Bypass -Scope Process -Force; irm https://agent-runtime-layer.vercel.app/install.ps1 | iex

$ErrorActionPreference = "Stop"
$DASHBOARD_URL = "http://localhost:4001"
$COMPOSE_URL   = "https://agent-runtime-layer.vercel.app/docker-compose.yml"
$INSTALL_DIR   = "$env:USERPROFILE\.agentium"

function Log($msg)  { Write-Host "  [OK] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Step($msg) { Write-Host "`n>> $msg" -ForegroundColor White }
function Fail($msg) { Write-Host "  [ERROR] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  +----------------------------------+" -ForegroundColor Cyan
Write-Host "  |       Agentium Installer         |" -ForegroundColor Cyan
Write-Host "  |  Free to observe. Pay to save.   |" -ForegroundColor Cyan
Write-Host "  +----------------------------------+" -ForegroundColor Cyan
Write-Host ""

# ── Helper: find Python executable ───────────────────────────
function Find-Python {
  # Check common commands first
  foreach ($cmd in @("python3", "python")) {
    try {
      $p = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
      if ($p) { return $p }
    } catch {}
  }
  # Search known install locations
  $bases = @(
    "$env:LOCALAPPDATA\Programs\Python",
    "$env:PROGRAMFILES\Python",
    "$env:PROGRAMFILES (x86)\Python"
  )
  foreach ($base in $bases) {
    if (Test-Path $base) {
      $found = Get-ChildItem $base -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($found) { return $found.FullName }
    }
  }
  # Check PATH entries
  foreach ($dir in $env:PATH.Split(";")) {
    $p = Join-Path $dir "python.exe"
    if (Test-Path $p) { return $p }
  }
  return $null
}

# ── 1. Docker check ──────────────────────────────────────────
Step "Checking Docker..."
try {
  $dockerInfo = docker info 2>$null
  Log "Docker is running"
} catch {
  Write-Host ""
  Write-Host "  Docker Desktop is not running or not installed." -ForegroundColor Yellow
  Write-Host ""
  Write-Host "  Install Docker Desktop (one-time setup):" -ForegroundColor White
  Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "  Once Docker Desktop is running, run this command again." -ForegroundColor White
  Start-Process "https://www.docker.com/products/docker-desktop/"
  exit 1
}

# ── 2. Download + start Agentium ────────────────────────────
Step "Downloading Agentium..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
Invoke-WebRequest -Uri $COMPOSE_URL -OutFile "$INSTALL_DIR\docker-compose.yml" -UseBasicParsing
Log "Configuration downloaded"

Step "Starting Agentium..."
Push-Location $INSTALL_DIR
docker compose pull --quiet 2>$null
docker compose up -d 2>$null
Pop-Location
Log "Dashboard running at $DASHBOARD_URL"

# ── 3. Python ────────────────────────────────────────────────
Step "Checking Python..."
$PYTHON = Find-Python

if (-not $PYTHON) {
  Warn "Python not found. Installing via winget..."
  try {
    winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements 2>$null
    # Refresh PATH from registry
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
    $PYTHON = Find-Python
  } catch {
    Warn "winget install failed. Trying direct download..."
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe" -OutFile $pythonInstaller -UseBasicParsing
    Start-Process $pythonInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1" -Wait
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
    $PYTHON = Find-Python
  }
}

if (-not $PYTHON) {
  Fail "Python could not be installed automatically. Install from https://python.org/downloads then re-run."
}
Log "Python found: $PYTHON"

# ── 4. Install SDK ───────────────────────────────────────────
Step "Installing Agentium SDK..."
& $PYTHON -m pip install agentium-tracer --quiet --upgrade
if ($LASTEXITCODE -ne 0) { Fail "SDK install failed. Check your Python installation." }
Log "SDK installed (agentium-tracer)"

# ── 5. Install hooks globally ────────────────────────────────
Step "Installing hooks for Claude Code + Codex (global)..."
& $PYTHON -m agent_runtime_layer.cli integrations install claude-code --global 2>$null
if ($LASTEXITCODE -eq 0) { Log "Claude Code hooks installed globally" }
else { Warn "Claude Code hook install skipped" }

& $PYTHON -m agent_runtime_layer.cli integrations install codex --global 2>$null
if ($LASTEXITCODE -eq 0) { Log "Codex hooks installed globally" }
else { Warn "Codex hook install skipped" }

# ── Set ANTHROPIC_BASE_URL + OPENAI_BASE_URL (Context Memory proxy) ─────────
Step "Configuring Context Memory proxy..."
$PROXY_URL = "http://localhost:8100"

function Set-EnvPermanent($Name, $Value) {
    # Set for current session
    [System.Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    # Set for current user permanently (survives reboots)
    [System.Environment]::SetEnvironmentVariable($Name, $Value, "User")
    # Also add to PowerShell profile for terminal sessions
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Force -Path $profileDir | Out-Null }
    if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
    $line = "`$env:$Name = '$Value'"
    if (-not (Select-String -Path $PROFILE -Pattern "env:$Name" -Quiet 2>$null)) {
        Add-Content -Path $PROFILE -Value "`n# Agentium Context Memory Proxy`n$line"
    }
}

Set-EnvPermanent "ANTHROPIC_BASE_URL" $PROXY_URL
Log "ANTHROPIC_BASE_URL=$PROXY_URL  (Claude Code routes through proxy)"
Set-EnvPermanent "OPENAI_BASE_URL" $PROXY_URL
Log "OPENAI_BASE_URL=$PROXY_URL     (Codex routes through proxy)"
Warn "Restart your terminal for proxy env vars to apply to new sessions"

# ── Done ────────────────────────────────────────────────────
Write-Host ""
Write-Host "  [OK] Agentium is live!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard -> $DASHBOARD_URL" -ForegroundColor White
Write-Host "  Proxy     -> $PROXY_URL  (caches stable context at `$0.30/MTok)" -ForegroundColor White
Write-Host ""
Write-Host "  Run Claude Code or Codex normally — traces appear in" -ForegroundColor Gray
Write-Host "  the dashboard. Stable context is cached automatically." -ForegroundColor Gray
Write-Host "  Open a new terminal for the proxy env vars to apply." -ForegroundColor Gray
Write-Host ""
Start-Process $DASHBOARD_URL
