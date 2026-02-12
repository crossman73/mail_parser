#!/usr/bin/env bash
set -euo pipefail
# =============================================================================
# Docker & Codacy 저장 공간 최적화 스크립트
# 용도: C: 드라이브 공간 절약을 위한 Docker/Codacy 정리
# 사용법: bash tools/docker_optimize.sh [setup|clean|status|full]
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CODACY_CACHE="$HOME/.cache/codacy"

# ─── 상태 확인 ───────────────────────────────────────────
show_status() {
    echo -e "${YELLOW}=== 디스크 상태 ===${NC}"
    df -h /mnt/c / 2>/dev/null | grep -E "Filesystem|/mnt/c|/$"

    echo -e "\n${YELLOW}=== Docker 사용량 ===${NC}"
    docker system df 2>/dev/null || echo "Docker 접근 불가"

    echo -e "\n${YELLOW}=== Codacy 캐시 ===${NC}"
    if [ -d "$CODACY_CACHE" ]; then
        du -sh "$CODACY_CACHE"/ 2>/dev/null
        du -sh "$CODACY_CACHE"/*/ 2>/dev/null
    else
        echo "캐시 없음"
    fi

    echo -e "\n${YELLOW}=== Docker 이미지 ===${NC}"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "없음"
}

# ─── Docker 정리 ─────────────────────────────────────────
clean_docker() {
    echo -e "${GREEN}[1/4] 중지된 컨테이너 정리...${NC}"
    docker container prune -f 2>/dev/null || true

    echo -e "${GREEN}[2/4] 사용하지 않는 이미지 정리...${NC}"
    docker image prune -a -f 2>/dev/null || true

    echo -e "${GREEN}[3/4] 사용하지 않는 볼륨 정리...${NC}"
    docker volume prune -f 2>/dev/null || true

    echo -e "${GREEN}[4/4] 빌드 캐시 정리...${NC}"
    docker builder prune -a -f 2>/dev/null || true

    echo -e "${GREEN}Docker 전체 정리 완료${NC}"
    docker system df 2>/dev/null
}

# ─── Codacy 캐시 정리 ────────────────────────────────────
clean_codacy_cache() {
    echo -e "${GREEN}Codacy 캐시 정리 중...${NC}"

    if [ -d "$CODACY_CACHE" ]; then
        local before
        before=$(du -sb "$CODACY_CACHE" 2>/dev/null | cut -f1)

        # runtimes 캐시 정리 (가장 큼: ~862MB)
        if [ -d "$CODACY_CACHE/runtimes" ]; then
            echo "  - runtimes 캐시 삭제 (재분석 시 자동 다운로드)"
            rm -rf "$CODACY_CACHE/runtimes"
        fi

        # tools 캐시 정리 (~565MB)
        if [ -d "$CODACY_CACHE/tools" ]; then
            echo "  - tools 캐시 삭제 (재분석 시 자동 다운로드)"
            rm -rf "$CODACY_CACHE/tools"
        fi

        # CLI tar.gz 파일 정리 (설치 후 불필요)
        find "$CODACY_CACHE" -name "*.tar.gz" -delete 2>/dev/null

        local after
        after=$(du -sb "$CODACY_CACHE" 2>/dev/null | cut -f1)
        local saved=$(( (before - after) / 1024 / 1024 ))
        echo -e "${GREEN}Codacy 캐시: ${saved}MB 절약${NC}"
    else
        echo "Codacy 캐시 없음"
    fi
}

# ─── /tmp 정리 ───────────────────────────────────────────
clean_tmp() {
    echo -e "${GREEN}/tmp 내 Codacy 잔여 파일 정리...${NC}"
    rm -rf /tmp/codacy-* /tmp/.codacy* 2>/dev/null || true
    # Docker 관련 임시 파일
    rm -rf /tmp/docker-* 2>/dev/null || true
}

# ─── Docker daemon.json 설정 (sudo 필요) ────────────────
setup_daemon() {
    echo -e "${YELLOW}Docker daemon.json 설정 (sudo 필요)${NC}"

    if [ -f /etc/docker/daemon.json ]; then
        echo -e "${YELLOW}기존 daemon.json 백업...${NC}"
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    fi

    sudo tee /etc/docker/daemon.json > /dev/null << 'DAEMON_EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "5m",
    "max-file": "2"
  },
  "storage-driver": "overlay2",
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "1GB"
    }
  }
}
DAEMON_EOF

    echo -e "${GREEN}daemon.json 생성 완료${NC}"
    echo "Docker 재시작 중..."
    sudo systemctl restart docker 2>/dev/null || sudo service docker restart 2>/dev/null || true
    echo -e "${GREEN}Docker 재시작 완료${NC}"
}

# ─── Codacy 도구 최적화 (.codacy/codacy.yaml) ───────────
optimize_codacy_tools() {
    local config_file="/mnt/c/dev/python-email/.codacy/codacy.yaml"
    if [ -f "$config_file" ]; then
        echo -e "${GREEN}Codacy 도구 설정 최적화...${NC}"
        # Python 프로젝트에 불필요한 도구 비활성화하여 이미지 다운로드 최소화
        cat > "$config_file" << 'YAML_EOF'
runtimes:
    - python@3.11.11
tools:
    - pylint@3.3.9
    - semgrep@1.78.0
    - trivy@0.66.0
YAML_EOF
        echo -e "${GREEN}불필요한 도구 제거: eslint, lizard, pmd (Java용), java, node 런타임${NC}"
        echo "  유지: pylint, semgrep, trivy (Python 프로젝트 필수)"
    fi
}

# ─── 전체 실행 ───────────────────────────────────────────
full_optimize() {
    echo -e "${RED}=== Docker & Codacy 전체 최적화 시작 ===${NC}"
    echo ""
    show_status
    echo ""
    clean_docker
    echo ""
    clean_codacy_cache
    echo ""
    clean_tmp
    echo ""
    optimize_codacy_tools
    echo ""
    echo -e "${RED}=== 최적화 완료 ===${NC}"
    show_status
}

# ─── 메인 ────────────────────────────────────────────────
case "${1:-status}" in
    setup)
        setup_daemon
        ;;
    clean)
        clean_docker
        clean_codacy_cache
        clean_tmp
        ;;
    status)
        show_status
        ;;
    full)
        setup_daemon
        full_optimize
        ;;
    *)
        echo "사용법: $0 [setup|clean|status|full]"
        echo "  setup  - Docker daemon.json 설정 (sudo 필요)"
        echo "  clean  - Docker/Codacy 정리만 실행"
        echo "  status - 현재 디스크 사용량 확인"
        echo "  full   - 전체 최적화 (setup + clean)"
        ;;
esac
