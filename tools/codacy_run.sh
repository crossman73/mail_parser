#!/usr/bin/env bash
set -euo pipefail
# Convenience script to ensure expected paths and run Codacy analysis via Docker
PROJECT_DIR="$(pwd)"

# Ensure templates path expected by Codacy
mkdir -p src/web/templates
for f in add_evidence.html integrated_timeline.html additional_evidence.html verify_integrity.html; do
  if [ ! -e "src/web/templates/$f" ]; then
    if [ -e "${PROJECT_DIR}/templates/$f" ]; then
      ln -sf "${PROJECT_DIR}/templates/$f" "src/web/templates/$f"
    fi
  fi
done

echo "Running Codacy Analysis (Docker)..."
docker run --rm --user "$(id -u)":"$(id -g)" \
  --env CODACY_CODE="${PROJECT_DIR}" \
  --env HOME=/tmp \
  --env XDG_CONFIG_HOME=/tmp \
  --workdir "${PROJECT_DIR}" \
  --volume "${PROJECT_DIR}":"${PROJECT_DIR}" \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume /tmp:/tmp \
  codacy/codacy-analysis-cli analyze --directory "${PROJECT_DIR}" --format text

echo "Codacy analysis finished."
