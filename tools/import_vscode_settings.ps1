<#
.SYNOPSIS
    VS Code 설정 가져오기 스크립트
.DESCRIPTION
    백업된 VS Code 설정을 현재 시스템에 적용합니다.
.EXAMPLE
    .\import_vscode_settings.ps1
    .\import_vscode_settings.ps1 -SettingsOnly
    .\import_vscode_settings.ps1 -ExtensionsOnly
#>

param(
    [switch]$SettingsOnly,     # 설정 파일만 가져오기
    [switch]$ExtensionsOnly,   # 확장만 설치
    [switch]$Force,            # 기존 설정 덮어쓰기
    [switch]$WhatIf            # 실제 적용하지 않고 미리보기
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backupDir = Join-Path $projectRoot "docs\vscode-settings-backup"

# VS Code 설정 경로
$userSettingsPath = "$env:APPDATA\Code\User\settings.json"
$userKeybindingsPath = "$env:APPDATA\Code\User\keybindings.json"

Write-Host "📥 VS Code 설정 가져오기" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

if (!(Test-Path $backupDir)) {
    Write-Host "❌ 백업 폴더가 없습니다: $backupDir" -ForegroundColor Red
    Write-Host "   먼저 export_vscode_settings.ps1을 실행해주세요." -ForegroundColor Yellow
    exit 1
}

# 1. 설정 파일 가져오기
if (!$ExtensionsOnly) {
    $latestSettings = Join-Path $backupDir "settings_latest.json"
    if (Test-Path $latestSettings) {
        if ($WhatIf) {
            Write-Host "🔍 [WhatIf] settings.json을 덮어쓸 예정" -ForegroundColor Yellow
        } else {
            if (!$Force -and (Test-Path $userSettingsPath)) {
                # 기존 설정 백업
                $backupPath = "$userSettingsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                Copy-Item $userSettingsPath $backupPath
                Write-Host "📦 기존 설정 백업: $backupPath" -ForegroundColor DarkGray
            }
            Copy-Item $latestSettings $userSettingsPath -Force
            Write-Host "✅ settings.json 적용 완료" -ForegroundColor Green
        }
    }
    
    $latestKeybindings = Join-Path $backupDir "keybindings_latest.json"
    if (Test-Path $latestKeybindings) {
        if ($WhatIf) {
            Write-Host "🔍 [WhatIf] keybindings.json을 덮어쓸 예정" -ForegroundColor Yellow
        } else {
            if (!$Force -and (Test-Path $userKeybindingsPath)) {
                $backupPath = "$userKeybindingsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                Copy-Item $userKeybindingsPath $backupPath
                Write-Host "📦 기존 키바인딩 백업: $backupPath" -ForegroundColor DarkGray
            }
            Copy-Item $latestKeybindings $userKeybindingsPath -Force
            Write-Host "✅ keybindings.json 적용 완료" -ForegroundColor Green
        }
    }
}

# 2. 확장 프로그램 설치
if (!$SettingsOnly) {
    $latestExtensions = Join-Path $backupDir "extensions_latest.txt"
    if (Test-Path $latestExtensions) {
        $extensions = Get-Content $latestExtensions | Where-Object { $_ -match '\S' }
        Write-Host "`n📦 확장 프로그램 설치 ($($extensions.Count)개)" -ForegroundColor Cyan
        
        if ($WhatIf) {
            Write-Host "🔍 [WhatIf] 다음 확장이 설치될 예정:" -ForegroundColor Yellow
            $extensions | ForEach-Object { Write-Host "   - $_" -ForegroundColor DarkGray }
        } else {
            $installed = 0
            $failed = 0
            
            foreach ($ext in $extensions) {
                Write-Host "   📥 $ext" -ForegroundColor White -NoNewline
                $result = & code --install-extension $ext --force 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host " ✅" -ForegroundColor Green
                    $installed++
                } else {
                    Write-Host " ❌" -ForegroundColor Red
                    $failed++
                }
            }
            
            Write-Host "`n   설치 완료: $installed, 실패: $failed" -ForegroundColor Cyan
        }
    }
}

Write-Host "`n"+"="*50 -ForegroundColor Cyan
if ($WhatIf) {
    Write-Host "🔍 미리보기 모드였습니다. 실제 적용하려면 -WhatIf 없이 실행하세요." -ForegroundColor Yellow
} else {
    Write-Host "✨ 설정 가져오기 완료! VS Code를 재시작하세요." -ForegroundColor Green
}
Write-Host "="*50 -ForegroundColor Cyan
