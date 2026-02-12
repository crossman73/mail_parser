#!/usr/bin/env bash
set -euo pipefail
# Convenience script to ensure expected paths and run Codacy analysis via Docker
# 최적화: 분석 후 Docker 이미지 자동 정리 (디스크 공간 절약)
PROJECT_DIR="$(pwd)"

# ─── 디스크 공간 체크 (최소 2GB 확보) ────────────────────
check_disk_space() {
  local avail_mb
  avail_mb=$(df --output=avail -BM /mnt/c 2>/dev/null | tail -1 | tr -d ' M')
  if [ -n "$avail_mb" ] && [ "$avail_mb" -lt 2048 ]; then
    echo "⚠️  경고: C: 드라이브 여유 공간 ${avail_mb}MB (최소 2GB 권장)"
    echo "   먼저 정리 실행: bash tools/docker_optimize.sh clean"
    # 2GB 미만이면 경고만 하고 계속 진행
  fi
}

# Ensure templates path expected by Codacy
mkdir -p src/web/templates
for f in add_evidence.html integrated_timeline.html additional_evidence.html verify_integrity.html; do
  if [ ! -e "src/web/templates/$f" ]; then
    if [ -e "${PROJECT_DIR}/templates/$f" ]; then
      ln -sf "${PROJECT_DIR}/templates/$f" "src/web/templates/$f"
    fi
  fi
done

check_disk_space

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
exit_code=$?

echo "Codacy analysis finished."

# ─── 분석 후 자동 정리 (디스크 공간 절약) ────────────────
echo "🧹 Docker 정리 중..."
# 중지된 컨테이너 정리
docker container prune -f 2>/dev/null || true
# dangling 이미지만 정리 (다음 실행 시 pull 시간 절약)
docker image prune -f 2>/dev/null || true
# /tmp 내 Codacy 임시 파일 정리
rm -rf /tmp/codacy-* /tmp/.codacy* 2>/dev/null || true
echo "✅ 정리 완료"

exit ${exit_code:-0}
