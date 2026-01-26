#!/usr/bin/env bash
cd /mnt/c/dev/python-email || exit 1
while true; do
  echo "----- $(date '+%Y-%m-%d %H:%M:%S') -----"
  if [ -f codacy_run.log ]; then
    stat -c '%y %s %n' codacy_run.log || true
  else
    echo 'codacy_run.log: missing'
  fi
  echo '--- docker ps (codacy) ---'
  docker ps --filter ancestor=codacy/codacy-analysis-cli:stable --format 'table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}' || true
  echo '--- last 50 lines of codacy_run.log ---'
  tail -n 50 codacy_run.log || true
  sleep 60
done
