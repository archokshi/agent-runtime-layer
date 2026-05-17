#!/usr/bin/env bash
set -e

MINT="\033[38;5;43m"
RED="\033[31m"
YELLOW="\033[33m"
BOLD="\033[1m"
RESET="\033[0m"

INSTALL_DIR="$HOME/.agentium"

log()  { echo -e "${MINT}${BOLD}  ✓${RESET}  $1"; }
warn() { echo -e "${YELLOW}${BOLD}  ⚠${RESET}  $1"; }
step() { echo -e "\n${BOLD}$1${RESET}"; }

echo ""
echo -e "${BOLD}  Agentium Uninstaller${RESET}"
echo ""

# -- 1. Stop and remove containers ----------------------------------
step "🛑 Stopping Agentium services..."
if [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
  cd "$INSTALL_DIR"
  docker compose down -v 2>/dev/null && log "Containers stopped and volumes removed" || warn "Could not stop containers (may already be stopped)"
else
  warn "No docker-compose.yml found in $INSTALL_DIR — skipping container shutdown"
fi

# -- 2. Remove Docker images ----------------------------------------
step "🗑  Removing Docker images..."
docker rmi archokshi/backend:latest 2>/dev/null  && log "Removed archokshi/backend:latest"  || warn "Image archokshi/backend:latest not found locally"
docker rmi archokshi/dashboard:latest 2>/dev/null && log "Removed archokshi/dashboard:latest" || warn "Image archokshi/dashboard:latest not found locally"

# -- 3. Remove install directory ------------------------------------
step "📁 Removing $INSTALL_DIR..."
if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  log "Removed $INSTALL_DIR"
else
  warn "$INSTALL_DIR not found — already removed"
fi

# -- 4. Uninstall SDK -----------------------------------------------
step "🐍 Uninstalling Agentium SDK..."
if command -v pip3 &>/dev/null; then
  pip3 uninstall agentium-tracer -y 2>/dev/null && log "SDK uninstalled" || warn "SDK not found via pip3"
elif command -v pip &>/dev/null; then
  pip uninstall agentium-tracer -y 2>/dev/null && log "SDK uninstalled" || warn "SDK not found via pip"
else
  warn "pip not found — SDK may still be installed"
fi

# -- Done -----------------------------------------------------------
echo ""
echo -e "${MINT}${BOLD}  ✅  Agentium removed.${RESET}"
echo ""
echo "  Note: if you installed Claude Code or Codex hooks in any repos,"
echo "  remove them by running inside each repo:"
echo ""
echo "    agent-runtime integrations uninstall claude-code --repo ."
echo "    agent-runtime integrations uninstall codex --repo ."
echo ""
