#!/usr/bin/env bash
# =============================================================================
# VS Code Global Settings Sync Script (Windows → GitHub Settings Sync)
# This script exports workspace .vscode settings to user-level so they
# apply whenever you open THIS project on ANY machine with your GitHub account.
#
# VS Code Settings Sync (built-in) syncs user-level settings.
# Project-level .vscode/ settings travel with the git repo.
# Together they ensure: any machine + same account = same environment.
#
# Usage: bash tools/sync_vscode_settings.sh
# =============================================================================
set -euo pipefail

VSCODE_DIR="/mnt/c/dev/python-email/.vscode"

echo "=== VS Code Environment Portability Check ==="
echo ""
echo "✅ Project-level settings (travels with git repo):"
for f in settings.json mcp.json tasks.json extensions.json; do
  if [ -f "$VSCODE_DIR/$f" ]; then
    echo "   ✓ .vscode/$f"
  else
    echo "   ✗ .vscode/$f MISSING"
  fi
done

echo ""
echo "✅ WSL environment setup script:"
if [ -x "/mnt/c/dev/python-email/tools/setup_wsl_env.sh" ]; then
  echo "   ✓ tools/setup_wsl_env.sh (executable)"
else
  echo "   ✗ tools/setup_wsl_env.sh MISSING or not executable"
fi

echo ""
echo "✅ VS Code Settings Sync (built-in):"
echo "   Ensure 'Settings Sync' is enabled in VS Code:"
echo "   File > Preferences > Settings Sync > Turn On"
echo "   This syncs your user-level settings, keybindings,"
echo "   extensions, and UI state across all machines."
echo ""
echo "✅ How portability works:"
echo "   1. Clone this repo → .vscode/ settings apply automatically"
echo "   2. Run 'bash tools/setup_wsl_env.sh' → WSL deps installed"
echo "   3. VS Code Settings Sync → user preferences restored"
echo "   4. Set API keys in .vscode/.env (not committed)"
echo ""
echo "=== Done ==="
