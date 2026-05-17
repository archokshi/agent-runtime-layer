#!/usr/bin/env bash
set -e

# ─────────────────────────────────────────────────────────────
#  Agentium Installer
#  Usage: curl -sSL https://get.agentium.ai | bash
# ─────────────────────────────────────────────────────────────

MINT="\033[38;5;43m"
RED="\033[31m"
YELLOW="\033[33m"
BOLD="\033[1m"
RESET="\033[0m"

INSTALL_DIR="$HOME/.agentium"
COMPOSE_URL="https://agent-runtime-layer.vercel.app/docker-compose.yml"
DASHBOARD_URL="http://localhost:4001"

log()    { echo -e "${MINT}${BOLD}  ✓${RESET}  $1"; }
warn()   { echo -e "${YELLOW}${BOLD}  ⚠${RESET}  $1"; }
err()    { echo -e "${RED}${BOLD}  ✗${RESET}  $1"; }
step()   { echo -e "\n${BOLD}$1${RESET}"; }
banner() {
  echo ""
  echo -e "${MINT}${BOLD}"
  echo "   ┌─────────────────────────────────┐"
  echo "   │        Agentium Installer        │"
  echo "   │  Free to observe. Pay to save.   │"
  echo "   └─────────────────────────────────┘"
  echo -e "${RESET}"
}

# ── Detect OS ────────────────────────────────────────────────
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "mac"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "linux"
  elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ "$OS" == "Windows_NT" ]]; then
    echo "windows"
  else
    echo "unknown"
  fi
}

# ── Open browser ─────────────────────────────────────────────
open_browser() {
  local url=$1
  local os=$(detect_os)
  sleep 2
  if [[ "$os" == "mac" ]]; then
    open "$url" 2>/dev/null || true
  elif [[ "$os" == "linux" ]]; then
    xdg-open "$url" 2>/dev/null || \
    sensible-browser "$url" 2>/dev/null || \
    echo -e "  Open this URL in your browser: ${MINT}${url}${RESET}"
  fi
}

# ── Install Docker ───────────────────────────────────────────
install_docker_linux() {
  step "📦 Installing Docker Engine..."
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
    log "Docker Engine installed"
  elif command -v yum &>/dev/null; then
    sudo yum install -y -q yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker "$USER" || true
    log "Docker Engine installed"
  else
    # Fallback: official convenience script
    curl -fsSL https://get.docker.com | sudo sh
    sudo systemctl start docker
    sudo usermod -aG docker "$USER" || true
    log "Docker Engine installed"
  fi
}

install_docker_mac() {
  step "📦 Installing Docker Desktop for Mac..."
  if ! command -v brew &>/dev/null; then
    warn "Homebrew not found — installing it first..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  brew install --cask docker --quiet
  log "Docker Desktop installed"
  echo ""
  warn "One manual step required:"
  echo "  1. Open Docker Desktop from your Applications folder"
  echo "  2. Accept the license agreement"
  echo "  3. Wait for the whale 🐳 icon in your menu bar"
  echo ""
  read -rp "  Press ENTER once Docker Desktop is running... "
}

# ── Wait for Docker daemon ───────────────────────────────────
wait_for_docker() {
  step "⏳ Waiting for Docker daemon..."
  local attempts=0
  until docker info &>/dev/null; do
    attempts=$((attempts + 1))
    if [[ $attempts -gt 30 ]]; then
      err "Docker daemon didn't start in time."
      echo "  Make sure Docker Desktop is open and running, then try again."
      exit 1
    fi
    sleep 2
  done
  log "Docker is running"
}

# ── Check docker compose ─────────────────────────────────────
check_compose() {
  if docker compose version &>/dev/null; then
    return 0
  elif command -v docker-compose &>/dev/null; then
    return 0
  else
    err "docker compose not found."
    echo "  Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
  fi
}

# ── Run compose ───────────────────────────────────────────────
run_compose() {
  if docker compose version &>/dev/null; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# ── Main ─────────────────────────────────────────────────────
main() {
  banner

  local os=$(detect_os)

  # ── Windows check ────────────────────────────────────────
  if [[ "$os" == "windows" ]]; then
    echo ""
    warn "Windows detected."
    echo "  Please install Docker Desktop manually:"
    echo "  → https://www.docker.com/products/docker-desktop/"
    echo ""
    echo "  Then run Agentium with:"
    echo "  mkdir agentium && cd agentium"
    echo "  curl -O https://get.agentium.ai/docker-compose.yml"
    echo "  docker compose up -d"
    echo ""
    exit 0
  fi

  # ── Check / install Docker ──────────────────────────────
  step "🔍 Checking for Docker..."
  if command -v docker &>/dev/null && docker info &>/dev/null; then
    log "Docker is already running"
  elif command -v docker &>/dev/null; then
    warn "Docker is installed but not running."
    if [[ "$os" == "mac" ]]; then
      echo "  Opening Docker Desktop..."
      open -a Docker 2>/dev/null || true
      wait_for_docker
    else
      sudo systemctl start docker 2>/dev/null || true
      wait_for_docker
    fi
  else
    if [[ "$os" == "mac" ]]; then
      install_docker_mac
    elif [[ "$os" == "linux" ]]; then
      install_docker_linux
    fi
    wait_for_docker
  fi

  check_compose

  # ── Download and start Agentium ─────────────────────────
  step "📥 Downloading Agentium..."
  mkdir -p "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  curl -fsSL "$COMPOSE_URL" -o docker-compose.yml
  log "Downloaded configuration"

  step "🚀 Starting Agentium..."
  run_compose pull --quiet
  run_compose up -d
  log "All services started"

  # ── Install Python if missing ────────────────────────────
  install_python() {
    if [[ "$os" == "mac" ]]; then
      step "🐍 Installing Python..."
      if command -v brew &>/dev/null; then
        brew install python --quiet && log "Python installed via Homebrew"
      else
        warn "Homebrew not found — installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        brew install python --quiet && log "Python installed via Homebrew"
      fi
    elif [[ "$os" == "linux" ]]; then
      step "🐍 Installing Python..."
      if command -v apt-get &>/dev/null; then
        sudo apt-get install -y -qq python3 python3-pip && log "Python installed"
      elif command -v yum &>/dev/null; then
        sudo yum install -y -q python3 python3-pip && log "Python installed"
      fi
    fi
  }

  # ── Install SDK ──────────────────────────────────────────
  step "🐍 Installing Agentium SDK..."

  # Auto-install Python if not found
  if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    install_python
  fi

  # Install SDK
  local pip_cmd=""
  if command -v pip3 &>/dev/null; then pip_cmd="pip3"
  elif command -v pip &>/dev/null; then pip_cmd="pip"
  fi

  if [[ -n "$pip_cmd" ]]; then
    $pip_cmd install agentium-tracer --quiet 2>/dev/null && log "SDK installed" || warn "SDK install failed — run manually: pip3 install agentium-tracer"
  else
    warn "Python still not found. Install from https://python.org/downloads then run: pip3 install agentium-tracer"
  fi

  # ── Install hooks globally ───────────────────────────────
  step "🔗 Installing agent hooks globally..."

  if command -v agent-runtime &>/dev/null; then
    agent-runtime integrations install claude-code --global 2>/dev/null && log "Claude Code hooks installed globally (~/.claude/settings.json)" || true
    agent-runtime integrations install codex --global 2>/dev/null && log "Codex hooks installed globally" || true
  else
    warn "SDK not in PATH yet — open a new terminal and run:"
    echo "    agent-runtime integrations install claude-code --global"
    echo "    agent-runtime integrations install codex --global"
  fi

  # ── Done ─────────────────────────────────────────────────
  echo ""
  echo -e "${MINT}${BOLD}  ✅  Agentium is live!${RESET}"
  echo ""
  echo -e "  Dashboard → ${BOLD}${DASHBOARD_URL}${RESET}"
  echo ""
  echo "  Run your agent normally — traces appear in the dashboard automatically."
  echo ""

  open_browser "$DASHBOARD_URL"
}

main "$@"
