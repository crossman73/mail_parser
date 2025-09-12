@echo off
REM Git Hook 설치 스크립트 (Windows)
REM Phase 2.4: 개발 환경 설정

echo 🔧 Git Hook 설치 시작...

REM .git/hooks 디렉토리 확인
if not exist ".git\hooks" (
    echo ❌ Git 저장소가 아니거나 .git\hooks 디렉토리가 없습니다.
    exit /b 1
)

REM Pre-commit hook 설치
echo 📄 Pre-commit hook 설치 중...
copy ".github\hooks\pre-commit" ".git\hooks\pre-commit" >nul

if %errorlevel% neq 0 (
    echo ❌ Pre-commit hook 설치 실패
    exit /b 1
)

echo ✅ Git Hook 설치 완료!
echo.
echo 📋 설치된 Hook:
echo   - Pre-commit: 커밋 시 자동 문서 생성
echo.
echo 🔄 이제 Python 파일을 수정하고 커밋하면 자동으로 문서가 업데이트됩니다.

pause
