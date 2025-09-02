@echo off
chcp 65001 > nul
echo ====================================
echo 이메일 파서 웹 서버 시작
echo ====================================

:: 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

:: Python 가상환경 활성화 (있는 경우)
if exist ".venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
)

:: 서버 실행 중인지 확인
netstat -ano | findstr ":5000" > nul
if %errorlevel% == 0 (
    echo 포트 5000이 이미 사용 중입니다.
    echo 기존 서버를 종료하시겠습니까? [Y/N]
    set /p answer=
    if /i "%answer%" == "Y" (
        echo 기존 서버 종료 중...
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5000"') do taskkill /F /PID %%i > nul 2>&1
        timeout /t 2 > nul
    ) else (
        echo 서버 시작을 취소합니다.
        pause
        exit /b
    )
)

:: 데이터베이스 초기화 확인
echo 데이터베이스 연결 확인 중...
python -c "from src.database.email_db import db; print('DB 연결 성공')" 2>nul
if %errorlevel% neq 0 (
    echo 데이터베이스 연결 실패. 모듈을 확인해주세요.
    pause
    exit /b 1
)

:: 백그라운드에서 서버 시작
echo 서버를 백그라운드에서 시작합니다...
start /b python -c "from src.web.app import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000, debug=False)" > server.log 2>&1

:: 서버 시작 대기
echo 서버 시작 대기 중...
timeout /t 3 > nul

:: 서버 시작 확인
netstat -ano | findstr ":5000" > nul
if %errorlevel% == 0 (
    echo ✅ 서버가 성공적으로 시작되었습니다!
    echo 📍 주소: http://localhost:5000
    echo 📍 관리자: http://localhost:5000/admin
    echo 📄 로그: server.log 파일을 확인하세요
    echo.
    echo 서버를 종료하려면 stop_server.bat을 실행하세요.
) else (
    echo ❌ 서버 시작에 실패했습니다.
    echo 📄 server.log 파일을 확인하세요.
    if exist server.log (
        echo.
        echo === 최근 로그 내용 ===
        tail server.log 2>nul || (
            echo 로그 내용을 확인할 수 없습니다.
            echo server.log 파일을 직접 열어서 확인해주세요.
        )
    )
    pause
    exit /b 1
)

echo.
pause
