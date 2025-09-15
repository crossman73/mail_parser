# 개발용 서버 시작 스크립트 (PowerShell)
# 이 스크립트는 개발 환경에서 풀 UI가 기본으로 활성화되게 하고
# 필요한 환경 변수를 설정한 뒤 개발 서버를 실행합니다.

param(
    [int]$Port = 5000,
    [switch]$AutoKill
)

# 개발에서는 기본적으로 legacy full UI를 사용합니다. 필요 시 USE_MINIMAL_UI=1으로 변경하세요.
$env:USE_FULL_UI = '1'

if ($AutoKill) {
    $env:AUTO_KILL = '1'
}

Write-Host "Starting development server on port $Port (USE_FULL_UI=1)"
Write-Host "  Python: $($env:VIRTUAL_ENV)"

# Activate venv if available
if (Test-Path -Path .\.venv\Scripts\Activate.ps1) {
    Write-Host "Activating .venv"
    . .\.venv\Scripts\Activate.ps1
}

# Run server
.\.venv\Scripts\python.exe .\run_server.py --auto-kill
