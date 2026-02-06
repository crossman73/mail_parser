#!/usr/bin/env bash
# =============================================================================
# WSL Environment Setup Script for python-email project
# Run: bash tools/setup_wsl_env.sh
# =============================================================================
set -euo pipefail

PROJECT_DIR="/mnt/c/dev/python-email"
VENV_DIR="${PROJECT_DIR}/.venv"

echo "=== WSL Environment Setup ==="

# 1. System packages
echo "[1/6] Checking system packages..."
PKGS_NEEDED=""
command -v python3 >/dev/null || PKGS_NEEDED="$PKGS_NEEDED python3"
command -v pip3 >/dev/null   || PKGS_NEEDED="$PKGS_NEEDED python3-pip"
command -v node >/dev/null   || PKGS_NEEDED="$PKGS_NEEDED nodejs npm"
command -v git >/dev/null    || PKGS_NEEDED="$PKGS_NEEDED git"
python3 -c "import venv" 2>/dev/null || PKGS_NEEDED="$PKGS_NEEDED python3-venv"

if [ -n "$PKGS_NEEDED" ]; then
  echo "  Installing:$PKGS_NEEDED"
  sudo apt-get update -qq && sudo apt-get install -y -qq $PKGS_NEEDED
else
  echo "  All system packages OK"
fi

# 2. Node/npm check
echo "[2/6] Node.js environment..."
echo "  node $(node --version) | npm $(npm --version)"

# 3. uv/uvx check (for serena MCP)
echo "[3/6] uv/uvx (Python tool runner)..."
if ! command -v uvx >/dev/null; then
  echo "  Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "  uvx: $(which uvx)"

# 4. Python virtual environment
echo "[4/6] Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  echo "  Created .venv"
fi
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
  pip install --quiet -r "$PROJECT_DIR/requirements.txt"
  echo "  Dependencies installed"
fi

# 5. Environment variables (WSL-side)
echo "[5/6] Environment variables..."
ENV_FILE="${PROJECT_DIR}/.vscode/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "  Loaded from .vscode/.env"
else
  echo "  WARNING: .vscode/.env not found — MCP servers may lack API keys"
fi

# 6. Verify MCP dependencies
echo "[6/6] MCP server dependencies..."
for pkg in "@codacy/codacy-mcp" "@upstash/context7-mcp" "@anthropic/mcp-server-brave-search" "@anthropic/mcp-server-sequential-thinking"; do
  echo "  Caching: $pkg"
  npx -y "$pkg" --help >/dev/null 2>&1 || true
done

echo ""
echo "=== Setup Complete ==="
echo "  Python: $(python3 --version)"
echo "  Node:   $(node --version)"
echo "  npm:    $(npm --version)"
echo "  uv:     $(uv --version 2>/dev/null || echo 'n/a')"
echo "  venv:   $VENV_DIR"
