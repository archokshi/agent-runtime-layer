# Agentium Installer for Windows (PowerShell)
# Usage: irm https://agent-runtime-layer.vercel.app/install.ps1 | iex

$ErrorActionPreference = "Stop"

$MINT    = "Cyan"
$DASHBOARD_URL = "http://localhost:4001"
$COMPOSE_URL   = "https://agent-runtime-layer.vercel.app/docker-compose.yml"
$INSTALL_DIR   = "$env:USERPROFILE\.agentium"

function Log($msg)  { Write-Host "  [OK] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Step($msg) { Write-Host "`n$msg" -ForegroundColor White }

Write-Host ""
Write-Host "  +---------------------------------+" -ForegroundColor Cyan
Write-Host "  |      Agentium Installer         |" -ForegroundColor Cyan
Write-Host "  |  Free to observe. Pay to save.  |" -ForegroundColor Cyan
Write-Host "  +---------------------------------+" -ForegroundColor Cyan
Write-Host ""

# -- 1. Check Docker ---------------------------------------------------
Step "Checking for Docker..."
try {
    $null = docker info 2>$null
    Log "Docker is already running"
} catch {
    Write-Host "  Docker not found or not running." -ForegroundColor Yellow
    Write-Host "  Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "  Then re-run this installer." -ForegroundColor Yellow
    exit 1
}

# -- 2. Download and start Agentium -----------------------------------
Step "Downloading Agentium..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
Invoke-WebRequest -Uri $COMPOSE_URL -OutFile "$INSTALL_DIR\docker-compose.yml" -UseBasicParsing
Log "Downloaded configuration"

Step "Starting Agentium..."
Set-Location $INSTALL_DIR
docker compose pull --quiet
docker compose up -d
Log "All services started"

# -- 3. Check / install Python -----------------------------------------
Step "Checking for Python..."
$pipCmd = $null
if (Get-Command pip3 -ErrorAction SilentlyContinue) {
    $pipCmd = "pip3"
    Log "Python found (pip3)"
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    $pipCmd = "pip"
    Log "Python found (pip)"
} else {
    Warn "Python not found. Installing via winget..."
    try {
        winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        if (Get-Command pip3 -ErrorAction SilentlyContinue) { $pipCmd = "pip3" }
        elseif (Get-Command pip -ErrorAction SilentlyContinue) { $pipCmd = "pip" }
        Log "Python installed"
    } catch {
        Warn "Could not auto-install Python. Install from https://python.org/downloads then re-run."
        $pipCmd = $null
    }
}

# -- 4. Install SDK ----------------------------------------------------
Step "Installing Agentium SDK..."
if ($pipCmd) {
    & $pipCmd install agentium-tracer --quiet
    Log "SDK installed (agentium-tracer)"
} else {
    Warn "Skipped — install Python first, then run: pip install agentium-tracer"
}

# -- 5. Install hooks globally -----------------------------------------
Step "Installing agent hooks globally..."
if (Get-Command agent-runtime -ErrorAction SilentlyContinue) {
    agent-runtime integrations install claude-code --global
    Log "Claude Code hooks installed globally"
    agent-runtime integrations install codex --global
    Log "Codex hooks installed globally"
} else {
    Warn "SDK not in PATH yet. Open a new terminal and run:"
    Write-Host "    agent-runtime integrations install claude-code --global"
    Write-Host "    agent-runtime integrations install codex --global"
}

# -- Done --------------------------------------------------------------
Write-Host ""
Write-Host "  [OK] Agentium is live!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard -> $DASHBOARD_URL"
Write-Host ""
Write-Host "  Run your agent normally — traces appear in the dashboard automatically."
Write-Host ""
Start-Process $DASHBOARD_URL
