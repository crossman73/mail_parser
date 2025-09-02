@echo off
chcp 65001 > nul
echo ====================================
echo 이메일 파서 웹 서버 종료
echo ====================================

:: 포트 5000을 사용하는 프로세스 찾기
echo 서버 프로세스 확인 중...
netstat -ano | findstr ":5000" > temp_processes.txt

if %errorlevel% neq 0 (
    echo ✅ 실행 중인 서버가 없습니다.
    if exist temp_processes.txt del temp_processes.txt
    pause
    exit /b 0
)

echo 다음 프로세스들이 포트 5000을 사용하고 있습니다:
type temp_processes.txt

echo.
echo 모든 서버 프로세스를 종료하시겠습니까? [Y/N]
set /p answer=

if /i "%answer%" neq "Y" (
    echo 서버 종료를 취소했습니다.
    if exist temp_processes.txt del temp_processes.txt
    pause
    exit /b 0
)

echo 서버 종료 중...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5000"') do (
    echo PID %%i 종료 중...
    taskkill /F /PID %%i > nul 2>&1
)

:: 정리
if exist temp_processes.txt del temp_processes.txt

:: 종료 확인
timeout /t 2 > nul
netstat -ano | findstr ":5000" > nul
if %errorlevel% neq 0 (
    echo ✅ 서버가 성공적으로 종료되었습니다.
) else (
    echo ⚠️  일부 프로세스가 여전히 실행 중일 수 있습니다.
    echo 수동으로 작업 관리자에서 확인해주세요.
)

echo.
pause
