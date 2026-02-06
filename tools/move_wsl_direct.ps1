#Requires -RunAsAdministrator
<#
.SYNOPSIS
    WSL Ubuntu를 C:\wsl로 직접 이동 (export/import 없이)
.DESCRIPTION
    1. WSL 종료
    2. vhdx 파일 직접 이동
    3. 레지스트리 경로 업데이트
    4. Windows Defender 제외 설정
.NOTES
    관리자 권한 필요. 추가 디스크 공간 불필요.
    작성일: 2026-02-02
#>

$ErrorActionPreference = "Stop"

$oldGuid = "{a7661f92-5853-4e7c-8922-cae2aec482c7}"
$oldPath = "C:\Users\cross\AppData\Local\wsl\$oldGuid"
$newPath = "C:\wsl\Ubuntu"
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\$oldGuid"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL 직접 이동 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "원본: $oldPath" -ForegroundColor Yellow
Write-Host "대상: $newPath" -ForegroundColor Yellow
Write-Host ""

# Step 1: WSL 종료
Write-Host "[1/5] WSL 종료 중..." -ForegroundColor Green
wsl --shutdown
Start-Sleep -Seconds 3
Write-Host "  WSL 종료됨" -ForegroundColor Gray

# Step 2: 대상 폴더 생성
Write-Host ""
Write-Host "[2/5] 대상 폴더 생성..." -ForegroundColor Green
if (!(Test-Path "C:\wsl")) {
    New-Item -ItemType Directory -Path "C:\wsl" -Force | Out-Null
}
if (!(Test-Path $newPath)) {
    New-Item -ItemType Directory -Path $newPath -Force | Out-Null
}
Write-Host "  폴더 생성됨: $newPath" -ForegroundColor Gray

# Step 3: 파일 이동
Write-Host ""
Write-Host "[3/5] vhdx 파일 이동 중 (시간이 걸릴 수 있습니다)..." -ForegroundColor Green
$moveStart = Get-Date

# 파일 목록 확인
$files = Get-ChildItem -Path $oldPath -Force
foreach ($file in $files) {
    Write-Host "  이동 중: $($file.Name)" -ForegroundColor Gray
    Move-Item -Path $file.FullName -Destination $newPath -Force
}

$moveDuration = (Get-Date) - $moveStart
Write-Host "  이동 완료! (소요시간: $($moveDuration.TotalSeconds.ToString('F1'))초)" -ForegroundColor Gray

# Step 4: 레지스트리 업데이트
Write-Host ""
Write-Host "[4/5] 레지스트리 경로 업데이트..." -ForegroundColor Green
try {
    Set-ItemProperty -Path $regPath -Name "BasePath" -Value $newPath
    Write-Host "  레지스트리 업데이트됨" -ForegroundColor Gray
} catch {
    Write-Host "  레지스트리 업데이트 실패: $_" -ForegroundColor Red
    Write-Host "  수동으로 실행하세요:" -ForegroundColor Yellow
    Write-Host "  reg add `"HKCU\Software\Microsoft\Windows\CurrentVersion\Lxss\$oldGuid`" /v BasePath /t REG_SZ /d `"$newPath`" /f" -ForegroundColor Yellow
}

# Step 5: Windows Defender 제외
Write-Host ""
Write-Host "[5/5] Windows Defender 제외 설정..." -ForegroundColor Green
$excludePaths = @("C:\wsl", "\\wsl$", "\\wsl.localhost")
$excludeProcesses = @("wsl.exe", "wslhost.exe", "python.exe", "node.exe")

foreach ($path in $excludePaths) {
    try {
        Add-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
        Write-Host "  제외 추가: $path" -ForegroundColor Gray
    } catch {
        Write-Host "  [이미 존재 또는 실패] $path" -ForegroundColor DarkGray
    }
}

foreach ($proc in $excludeProcesses) {
    try {
        Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
        Write-Host "  프로세스 제외: $proc" -ForegroundColor Gray
    } catch {
        Write-Host "  [이미 존재 또는 실패] $proc" -ForegroundColor DarkGray
    }
}

# 정리
Write-Host ""
Write-Host "[정리] 빈 원본 폴더 삭제..." -ForegroundColor Green
try {
    Remove-Item -Path $oldPath -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "C:\Users\cross\AppData\Local\wsl" -Force -ErrorAction SilentlyContinue
    Write-Host "  원본 폴더 삭제됨" -ForegroundColor Gray
} catch {
    Write-Host "  원본 폴더 수동 삭제 필요" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "이동 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 확인
Write-Host "확인 중..." -ForegroundColor Yellow
wsl --list -v

Write-Host ""
Write-Host "새 위치 확인:" -ForegroundColor Yellow
Get-ChildItem -Path $newPath -Force | Format-Table Name, Length, LastWriteTime

Write-Host ""
Write-Host "테스트: wsl 명령으로 접속해보세요" -ForegroundColor Cyan
