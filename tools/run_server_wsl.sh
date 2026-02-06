#!/usr/bin/env bash
# Use set -e and pipefail but avoid -u to prevent unbound variable errors in diverse shells
set -eo pipefail
# WSL-friendly runner for the development server
# Usage: ./tools/run_server_wsl.sh [--port 5000] [--auto-kill] [--daemon]

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG="$ROOT/server_wsl.log"
PIDFILE="$ROOT/server_wsl.pid"

PORT=5000
AUTO_KILL=0
DAEMON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      shift; PORT="$1"; shift;;
    --auto-kill)
      AUTO_KILL=1; shift;;
    --daemon)
      DAEMON=1; shift;;
    --help|-h)
      echo "Usage: $0 [--port PORT] [--auto-kill] [--daemon]"; exit 0;;
    *)
      echo "Unknown arg: $1"; exit 2;;
  esac
done

echo "[run_server_wsl] Root: $ROOT"
echo "[run_server_wsl] Port: $PORT, AUTO_KILL=$AUTO_KILL, DAEMON=$DAEMON"

# Activate venv if available
if [ -f "$ROOT/.venv/bin/activate" ]; then
  # typical Linux venv
  # shellcheck disable=SC1090
  source "$ROOT/.venv/bin/activate"
  echo "[run_server_wsl] Activated .venv"
elif [ -f "$ROOT/venv/bin/activate" ]; then
  source "$ROOT/venv/bin/activate"
  echo "[run_server_wsl] Activated venv"
else
  echo "[run_server_wsl] No virtualenv found - using system python3"
fi

export FLASK_ENV=development
# Ensure AUTO_KILL has a default value for set -u
AUTO_KILL=${AUTO_KILL:-0}
if [ "${AUTO_KILL:-0}" -eq 1 ]; then
  export AUTO_KILL=1
else
  unset AUTO_KILL
fi

CMD=(python3 -m src.runner.run_server "--port" "$PORT")
if [ "${AUTO_KILL:-0}" -eq 1 ]; then
  CMD+=(--auto-kill)
fi

if [ "$DAEMON" -eq 1 ]; then
  echo "[run_server_wsl] Starting daemon: ${CMD[*]}"
  nohup "${CMD[@]}" > "$LOG" 2>&1 &
  PID=$!
  echo "$PID" > "$PIDFILE"
  echo "[run_server_wsl] Started background server (PID=$PID), log: $LOG"
  exit 0
else
  echo "[run_server_wsl] Starting foreground: ${CMD[*]}"
  exec "${CMD[@]}"
fi
