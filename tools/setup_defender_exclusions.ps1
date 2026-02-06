#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Windows Defender에서 WSL 및 개발 관련 경로 제외 설정
.DESCRIPTION
    WSL2 성능 최적화를 위한 Defender 제외 설정
    - C:\wsl 전체 (WSL 배포판)
    - node_modules 경로
    - Python 가상환경 경로
.NOTES
    관리자 권한으로 실행해야 합니다.
    작성일: 2026-02-02
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Defender 제외 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 제외할 폴더 경로
$excludePaths = @(
    # WSL 배포판 위치
    "C:\wsl",
    
    # WSL UNC 경로
    "\\wsl$",
    "\\wsl.localhost",
    
    # 현재 프로젝트 (python-email)
    "C:\dev\python-email\.venv",
    "C:\dev\python-email\node_modules",
    
    # 일반적인 개발 경로
    "C:\dev"
)

# 제외할 프로세스
$excludeProcesses = @(
    # WSL 관련
    "wsl.exe",
    "wslhost.exe",
    
    # Python 관련
    "python.exe",
    "python3.exe",
    "pip.exe",
    "pip3.exe",
    
    # Node.js 관련
    "node.exe",
    "npm.cmd",
    "pnpm.exe",
    
    # VS Code
    "Code.exe"
)

# 제외할 파일 확장자
$excludeExtensions = @(
    ".py",
    ".pyc",
    ".pyo",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".md"
)

Write-Host "[1/3] 폴더 경로 제외 추가 중..." -ForegroundColor Green
foreach ($path in $excludePaths) {
    try {
        # 이미 제외되어 있는지 확인
        $existingExclusions = Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
        if ($existingExclusions -contains $path) {
            Write-Host "  [이미 존재] $path" -ForegroundColor Gray
        } else {
            Add-MpPreference -ExclusionPath $path
            Write-Host "  [추가됨] $path" -ForegroundColor White
        }
    } catch {
        Write-Host "  [실패] $path - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[2/3] 프로세스 제외 추가 중..." -ForegroundColor Green
foreach ($process in $excludeProcesses) {
    try {
        $existingProcesses = Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
        if ($existingProcesses -contains $process) {
            Write-Host "  [이미 존재] $process" -ForegroundColor Gray
        } else {
            Add-MpPreference -ExclusionProcess $process
            Write-Host "  [추가됨] $process" -ForegroundColor White
        }
    } catch {
        Write-Host "  [실패] $process - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[3/3] 파일 확장자 제외 추가 중..." -ForegroundColor Green
foreach ($ext in $excludeExtensions) {
    try {
        $existingExtensions = Get-MpPreference | Select-Object -ExpandProperty ExclusionExtension
        if ($existingExtensions -contains $ext) {
            Write-Host "  [이미 존재] $ext" -ForegroundColor Gray
        } else {
            Add-MpPreference -ExclusionExtension $ext
            Write-Host "  [추가됨] $ext" -ForegroundColor White
        }
    } catch {
        Write-Host "  [실패] $ext - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 현재 제외 목록 표시
Write-Host "현재 Defender 제외 설정:" -ForegroundColor Yellow
Write-Host ""
Write-Host "폴더:" -ForegroundColor Cyan
(Get-MpPreference).ExclusionPath | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "프로세스:" -ForegroundColor Cyan
(Get-MpPreference).ExclusionProcess | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "확장자:" -ForegroundColor Cyan
(Get-MpPreference).ExclusionExtension | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "참고: 변경 사항은 즉시 적용됩니다." -ForegroundColor Yellow
