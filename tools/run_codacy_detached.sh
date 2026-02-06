#!/usr/bin/env bash
# Wrapper to start codacy-cli detached and reliably record PID
set -euo pipefail

OUT_DIR="/mnt/c/dev/python-email"
ANALYZE_LOG="$OUT_DIR/analyze_run_capture.log"
RESULT_LOG="$OUT_DIR/codacy_local_run.log"
PID_FILE="$OUT_DIR/codacy_cli_pid.txt"

export CODACY_CODE="$OUT_DIR"

# Rotate logs (keep last 1 copy)
if [ -f "$ANALYZE_LOG" ]; then mv "$ANALYZE_LOG" "${ANALYZE_LOG}.old" || true; fi
if [ -f "$RESULT_LOG" ]; then mv "$RESULT_LOG" "${RESULT_LOG}.old" || true; fi

# Start detached with setsid and record PID
setsid /home/crossman/.local/bin/codacy-cli analyze \
  --allow-network \
  --force-file-permissions \
  --skip-uncommitted-files-check \
  --format text \
  --output "$RESULT_LOG" \
  --verbose > "$ANALYZE_LOG" 2>&1 &

echo $! > "$PID_FILE"
echo "Started codacy-cli (detached) PID: $(cat "$PID_FILE")"
