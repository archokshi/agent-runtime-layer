#!/usr/bin/env bash
set -e

MINT="\033[38;5;43m"
RED="\033[31m"
YELLOW="\033[33m"
BOLD="\033[1m"
RESET="\033[0m"

INSTALL_DIR="$HOME/.agentium"
COMPOSE_URL="https://agent-runtime-layer.vercel.app/docker-compose.yml"
DASHBOARD_URL="http://localhost:4001"

log()  { echo -e "${MINT}${BOLD}  ✓${RESET}  $1"; }
warn() { echo -e "${YELLOW}${BOLD}  ⚠${RESET}  $1"; }
err()  { echo -e "${RED}${BOLD}  ✗${RESET}  $1"; }
step() { echo -e "\n${BOLD}$1${RESET}"; }

echo ""
echo -e "${MINT}${BOLD}"
echo "   ┌─────────────────────────────────┐"
echo "   │        Agentium Installer        │"
echo "   │  Free to observe. Pay to save.   │"
echo "   └─────────────────────────────────┘"
echo -e "${RESET}"

# ── Detect OS ────────────────────────────────────────────────
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then echo "mac"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then echo "linux"
  else echo "unknown"
  fi
}
OS=$(detect_os)

# ── Open browser ─────────────────────────────────────────────
open_browser() {
  sleep 2
  if [[ "$OS" == "mac" ]]; then
    open "$1" 2>/dev/null || true
  else
    xdg-open "$1" 2>/dev/null || sensible-browser "$1" 2>/dev/null || true
  fi
}

# ── Find Python executable ────────────────────────────────────
# Verifies each candidate actually runs — guards against Windows Store
# redirects that are found by `command -v` but fail when executed.
python_works() {
  local ver
  ver=$("$1" --version 2>&1) || return 1
  # Windows Store shim prints nothing or "Python was not found..."
  [[ "$ver" == Python\ 3* ]] || return 1
}

find_python() {
  # Try common command names, verify each actually works
  for cmd in python3 python python3.13 python3.12 python3.11 python3.10; do
    if command -v "$cmd" &>/dev/null && python_works "$cmd"; then
      echo "$cmd"; return
    fi
  done
  # macOS Homebrew paths
  for p in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if [[ -x "$p" ]] && python_works "$p"; then echo "$p"; return; fi
  done
  # Windows paths (Git Bash / MSYS)
  for p in \
    "/c/Python313/python.exe" "/c/Python312/python.exe" \
    "/c/Python311/python.exe" "/c/Python310/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python313/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python312/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" \
    "$USERPROFILE/AppData/Local/Programs/Python/Python310/python.exe"; do
    if [[ -x "$p" ]] && python_works "$p"; then echo "$p"; return; fi
  done
  echo ""
}

# ── Install Python ────────────────────────────────────────────
install_python() {
  step "🐍 Installing Python..."
  # Windows Git Bash / MSYS — use winget
  if [[ "$OS" == "unknown" ]] || [[ -n "$WINDIR" ]] || [[ -n "$USERPROFILE" ]]; then
    if command -v winget &>/dev/null; then
      winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements || true
      warn "Python installed. Open a new terminal and re-run the installer if the next step fails."
      return
    else
      warn "Could not auto-install Python on Windows."
      echo "  Install from https://python.org/downloads then re-run this command."
      exit 1
    fi
  fi
  if [[ "$OS" == "mac" ]]; then
    if ! command -v brew &>/dev/null; then
      warn "Installing Homebrew first..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      # Add Homebrew to PATH for this session
      eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
    fi
    brew install python --quiet
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
    log "Python installed"
  elif [[ "$OS" == "linux" ]]; then
    if command -v apt-get &>/dev/null; then
      sudo apt-get install -y -qq python3 python3-pip
    elif command -v yum &>/dev/null; then
      sudo yum install -y -q python3 python3-pip
    fi
    log "Python installed"
  fi
}

# ── Install Docker (Linux) ────────────────────────────────────
install_docker_linux() {
  step "🐳 Installing Docker..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker "$USER" || true
  elif command -v yum &>/dev/null; then
    sudo yum install -y -q yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker "$USER" || true
  else
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER" || true
  fi
  log "Docker installed"
}

install_docker_mac() {
  step "🐳 Installing Docker Desktop..."
  if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
  fi
  brew install --cask docker --quiet
  log "Docker Desktop installed"
  echo ""
  warn "Open Docker Desktop from your Applications folder, accept the license, then press ENTER."
  read -rp "  Press ENTER once the Docker whale 🐳 appears in your menu bar... "
}

wait_for_docker() {
  step "⏳ Waiting for Docker..."
  local attempts=0
  until docker info &>/dev/null 2>&1; do
    attempts=$((attempts+1))
    if [[ $attempts -gt 30 ]]; then
      err "Docker didn't start. Make sure Docker Desktop is open and try again."
      exit 1
    fi
    sleep 2
  done
  log "Docker is running"
}

# ── 1. Docker ────────────────────────────────────────────────
step "🔍 Checking Docker..."
if docker info &>/dev/null 2>&1; then
  log "Docker is already running"
elif command -v docker &>/dev/null; then
  warn "Docker installed but not running — starting it..."
  if [[ "$OS" == "mac" ]]; then
    open -a Docker 2>/dev/null || true
  else
    sudo systemctl start docker 2>/dev/null || true
  fi
  wait_for_docker
else
  if [[ "$OS" == "mac" ]]; then install_docker_mac
  elif [[ "$OS" == "linux" ]]; then install_docker_linux
  fi
  wait_for_docker
fi

# ── 2. Start Agentium ───────────────────────────────────────
step "📥 Downloading Agentium..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
curl -fsSL "$COMPOSE_URL" -o docker-compose.yml
log "Configuration downloaded"

step "🚀 Starting Agentium..."
if docker compose version &>/dev/null 2>&1; then
  docker compose pull --quiet
  docker compose up -d
else
  docker-compose pull --quiet
  docker-compose up -d
fi
log "Dashboard running at $DASHBOARD_URL"

# ── 3. Python ────────────────────────────────────────────────
step "🐍 Checking Python..."
PYTHON=$(find_python)
if [[ -z "$PYTHON" ]]; then
  install_python
  PYTHON=$(find_python)
fi

if [[ -n "$PYTHON" ]]; then
  log "Python found: $PYTHON"
else
  warn "Python not found — install from https://python.org/downloads and re-run."
  exit 1
fi

# ── 4. Install SDK ───────────────────────────────────────────
step "📦 Installing Agentium SDK..."
"$PYTHON" -m pip install agentium-tracer --quiet --upgrade
log "SDK installed"

# ── 5. Install hooks globally ────────────────────────────────
step "🔗 Installing hooks for Claude Code + Codex (global)..."
"$PYTHON" -m agent_runtime_layer.cli integrations install claude-code --global 2>/dev/null \
  && log "Claude Code hooks installed globally" \
  || warn "Claude Code hook install skipped"
"$PYTHON" -m agent_runtime_layer.cli integrations install codex --global 2>/dev/null \
  && log "Codex hooks installed globally" \
  || warn "Codex hook install skipped"

# ── Set ANTHROPIC_BASE_URL + OPENAI_BASE_URL (Context Memory proxy) ──────────
step "🔀 Configuring Context Memory proxy..."
PROXY_URL="http://localhost:8100"

set_env_in_rc() {
  local var="$1" val="$2"
  for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    [[ -f "$rc" ]] || continue
    if grep -q "^export ${var}=" "$rc" 2>/dev/null; then
      sed -i.bak "s|^export ${var}=.*|export ${var}=${val}|" "$rc"
    else
      printf '\n# Agentium Context Memory Proxy\nexport %s=%s\n' "$var" "$val" >> "$rc"
    fi
  done
  # Create .bashrc if no rc exists at all
  if [[ ! -f "$HOME/.bashrc" ]] && [[ ! -f "$HOME/.zshrc" ]]; then
    printf 'export %s=%s\n' "$var" "$val" >> "$HOME/.bashrc"
  fi
  export "${var}=${val}"
}

set_env_in_rc "ANTHROPIC_BASE_URL" "$PROXY_URL"
set_env_in_rc "OPENAI_BASE_URL"    "$PROXY_URL"
log "ANTHROPIC_BASE_URL=$PROXY_URL  (Claude Code routes through proxy)"
log "OPENAI_BASE_URL=$PROXY_URL     (Codex routes through proxy)"

# ── Done ────────────────────────────────────────────────────
echo ""
echo -e "${MINT}${BOLD}  ✅  Agentium is live!${RESET}"
echo ""
echo -e "  Dashboard → ${BOLD}${DASHBOARD_URL}${RESET}"
echo -e "  Proxy     → ${BOLD}${PROXY_URL}${RESET}  (caches stable context at \$0.30/MTok)"
echo ""
echo "  Run Claude Code or Codex normally — traces appear in"
echo "  the dashboard. Stable context is cached automatically."
echo "  Open a new terminal for the proxy env vars to apply."
echo ""

open_browser "$DASHBOARD_URL"
