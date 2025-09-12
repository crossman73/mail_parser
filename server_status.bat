@echo off
chcp 65001 > nul
echo ====================================
echo 이메일 파서 웹 서버 상태 확인
echo ====================================

:: 포트 확인
echo 📍 포트 5000 상태 확인:
netstat -ano | findstr ":5000"
if %errorlevel% neq 0 (
    echo   ❌ 서버가 실행되고 있지 않습니다.
    echo.
    echo 서버를 시작하려면 server_start.bat을 실행하세요.
) else (
    echo   ✅ 서버가 실행 중입니다.
    echo.
    echo 📍 접속 주소:
    echo   - 메인: http://localhost:5000
    echo   - 관리자: http://localhost:5000/admin
)

echo.
echo ====================================

:: HTTP 연결 테스트
echo 🔄 서버 응답 테스트 중...
curl -s -o nul -w "HTTP 상태: %%{http_code}" http://localhost:5000 2>nul
if %errorlevel% == 0 (
    echo   ✅ 서버 응답 정상
) else (
    echo   ❌ 서버 응답 없음 ^(curl 명령 필요^)
    echo   브라우저에서 http://localhost:5000 접속해보세요.
)

echo.
echo ====================================

:: 로그 파일 확인
if exist server.log (
    echo 📄 최근 서버 로그 (마지막 10줄):
    echo.
    tail server.log 2>nul
    if %errorlevel% neq 0 (
        echo 로그를 읽을 수 없습니다.
    )
) else (
    echo 📄 로그 파일이 없습니다.
)

echo.
echo ====================================
echo.

:: 데이터베이스 상태 확인
echo 💾 데이터베이스 상태:
python -c "from src.database.email_db import db; files = db.get_all_processed_files(); print(f'처리된 파일: {len(files)}개')" 2>nul
if %errorlevel% neq 0 (
    echo   ❌ 데이터베이스 연결 실패
) else (
    echo   ✅ 데이터베이스 연결 정상
)

echo.
pause
