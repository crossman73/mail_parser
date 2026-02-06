#Requires -RunAsAdministrator
<#
.SYNOPSIS
    WSL Ubuntu 배포판을 C:\wsl로 이동하는 스크립트
.DESCRIPTION
    1. WSL 종료
    2. 배포판 내보내기 (export)
    3. 배포판 등록 해제 (unregister)
    4. 새 위치에 가져오기 (import)
    5. 기본 사용자 설정
.NOTES
    관리자 권한으로 실행해야 합니다.
    작성일: 2026-02-02
#>

param(
    [string]$DistroName = "Ubuntu",
    [string]$TargetPath = "C:\wsl\Ubuntu",
    [string]$ExportPath = "C:\wsl\backup",
    [string]$DefaultUser = "crossman"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL 배포판 이동 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "대상 배포판: $DistroName" -ForegroundColor Yellow
Write-Host "이동 위치: $TargetPath" -ForegroundColor Yellow
Write-Host "기본 사용자: $DefaultUser" -ForegroundColor Yellow
Write-Host ""

# 1. 현재 WSL 상태 확인
Write-Host "[1/7] 현재 WSL 상태 확인..." -ForegroundColor Green
wsl --list --verbose

# 2. C:\wsl 디렉토리 생성
Write-Host ""
Write-Host "[2/7] 대상 디렉토리 생성..." -ForegroundColor Green
if (!(Test-Path $TargetPath)) {
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Write-Host "  생성됨: $TargetPath" -ForegroundColor Gray
}
if (!(Test-Path $ExportPath)) {
    New-Item -ItemType Directory -Path $ExportPath -Force | Out-Null
    Write-Host "  생성됨: $ExportPath" -ForegroundColor Gray
}

# 3. WSL 종료
Write-Host ""
Write-Host "[3/7] WSL 종료 중..." -ForegroundColor Green
wsl --shutdown
Start-Sleep -Seconds 3
Write-Host "  WSL이 종료되었습니다." -ForegroundColor Gray

# 4. 배포판 내보내기
$exportFile = Join-Path $ExportPath "$DistroName-backup.tar"
Write-Host ""
Write-Host "[4/7] 배포판 내보내기 (시간이 걸릴 수 있습니다)..." -ForegroundColor Green
Write-Host "  내보내기 경로: $exportFile" -ForegroundColor Gray

$exportStart = Get-Date
wsl --export $DistroName $exportFile
$exportDuration = (Get-Date) - $exportStart
Write-Host "  내보내기 완료! (소요시간: $($exportDuration.TotalMinutes.ToString('F1'))분)" -ForegroundColor Gray

# 내보내기 파일 크기 확인
$exportSize = (Get-Item $exportFile).Length / 1GB
Write-Host "  백업 파일 크기: $($exportSize.ToString('F2')) GB" -ForegroundColor Gray

# 5. 기존 배포판 등록 해제
Write-Host ""
Write-Host "[5/7] 기존 배포판 등록 해제..." -ForegroundColor Green
Write-Host "  경고: 이 작업은 기존 위치의 데이터를 삭제합니다!" -ForegroundColor Red
$confirm = Read-Host "  계속하시겠습니까? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "  작업이 취소되었습니다." -ForegroundColor Yellow
    Write-Host "  백업 파일은 보존됩니다: $exportFile" -ForegroundColor Yellow
    exit 0
}
wsl --unregister $DistroName
Write-Host "  등록 해제 완료!" -ForegroundColor Gray

# 6. 새 위치에 가져오기
Write-Host ""
Write-Host "[6/7] 새 위치에 배포판 가져오기..." -ForegroundColor Green
Write-Host "  대상 경로: $TargetPath" -ForegroundColor Gray

$importStart = Get-Date
wsl --import $DistroName $TargetPath $exportFile --version 2
$importDuration = (Get-Date) - $importStart
Write-Host "  가져오기 완료! (소요시간: $($importDuration.TotalMinutes.ToString('F1'))분)" -ForegroundColor Gray

# 7. 기본 사용자 설정
Write-Host ""
Write-Host "[7/7] 기본 사용자 설정..." -ForegroundColor Green

# /etc/wsl.conf에 기본 사용자 설정 추가
$wslConfContent = @"
[user]
default=$DefaultUser

[interop]
appendWindowsPath=true

[automount]
enabled=true
options="metadata,umask=22,fmask=11"
"@

# WSL 내에서 설정 파일 생성
wsl -d $DistroName -u root bash -c "echo '$wslConfContent' > /etc/wsl.conf"
Write-Host "  /etc/wsl.conf 설정 완료" -ForegroundColor Gray

# WSL 재시작하여 설정 적용
wsl --shutdown
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "이동 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "새 위치: $TargetPath" -ForegroundColor Cyan
Write-Host ""

# 최종 상태 확인
Write-Host "최종 WSL 상태:" -ForegroundColor Yellow
wsl --list --verbose

Write-Host ""
Write-Host "백업 파일 정리:" -ForegroundColor Yellow
Write-Host "  백업 파일: $exportFile" -ForegroundColor Gray
Write-Host "  이동이 성공적으로 완료되면 백업 파일을 삭제해도 됩니다." -ForegroundColor Gray
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Cyan
Write-Host "  1. 'wsl' 명령으로 접속하여 정상 동작 확인" -ForegroundColor White
Write-Host "  2. Windows Defender 제외 설정 추가 (C:\wsl)" -ForegroundColor White
Write-Host "  3. 백업 파일 삭제 (선택사항)" -ForegroundColor White
