#!/bin/bash
# Git Hook 설치 스크립트
# Phase 2.4: 개발 환경 설정

echo "🔧 Git Hook 설치 시작..."

# .git/hooks 디렉토리 확인
if [ ! -d ".git/hooks" ]; then
    echo "❌ Git 저장소가 아니거나 .git/hooks 디렉토리가 없습니다."
    exit 1
fi

# Pre-commit hook 설치
echo "📄 Pre-commit hook 설치 중..."
cp .github/hooks/pre-commit .git/hooks/pre-commit

# 실행 권한 부여 (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook 실행 권한 설정 완료"
fi

echo "🎉 Git Hook 설치 완료!"
echo ""
echo "📋 설치된 Hook:"
echo "  - Pre-commit: 커밋 시 자동 문서 생성"
echo ""
echo "🔄 이제 Python 파일을 수정하고 커밋하면 자동으로 문서가 업데이트됩니다."
