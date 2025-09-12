#!/bin/bash
# Docker 헬스체크 스크립트

# 웹 서버 응답 확인
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ 웹 서버 정상"
    exit 0
else
    echo "❌ 웹 서버 응답 없음"
    exit 1
fi

# NOTE:
# This script is used by Docker healthcheck in the compose configuration.
# For local development on low-resource machines, running Docker may be
# disabled to avoid heavy CPU/RAM/disk usage — see README.md for guidance.
