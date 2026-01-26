<#
.SYNOPSIS
    VS Code 설정 내보내기 스크립트
.DESCRIPTION
    현재 VS Code 사용자 설정을 프로젝트 docs 폴더로 내보냅니다.
.EXAMPLE
    .\export_vscode_settings.ps1
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$outputDir = Join-Path $projectRoot "docs\vscode-settings-backup"

# 출력 디렉토리 생성
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

# VS Code 설정 경로
$userSettingsPath = "$env:APPDATA\Code\User\settings.json"
$userKeybindingsPath = "$env:APPDATA\Code\User\keybindings.json"

Write-Host "📦 VS Code 설정 내보내기" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

# 1. 설정 파일 복사
if (Test-Path $userSettingsPath) {
    $destSettings = Join-Path $outputDir "settings_$timestamp.json"
    Copy-Item $userSettingsPath $destSettings
    Write-Host "✅ settings.json → $destSettings" -ForegroundColor Green
    
    # 최신 버전도 저장
    Copy-Item $userSettingsPath (Join-Path $outputDir "settings_latest.json") -Force
}

# 2. 키바인딩 복사
if (Test-Path $userKeybindingsPath) {
    $destKeybindings = Join-Path $outputDir "keybindings_$timestamp.json"
    Copy-Item $userKeybindingsPath $destKeybindings
    Write-Host "✅ keybindings.json → $destKeybindings" -ForegroundColor Green
    
    Copy-Item $userKeybindingsPath (Join-Path $outputDir "keybindings_latest.json") -Force
}

# 3. 확장 프로그램 목록 저장
$extensionsFile = Join-Path $outputDir "extensions_$timestamp.txt"
$extensions = & code --list-extensions
$extensions | Out-File $extensionsFile -Encoding utf8
Write-Host "✅ 확장 목록 ($($extensions.Count)개) → $extensionsFile" -ForegroundColor Green

# 최신 버전도 저장
$extensions | Out-File (Join-Path $outputDir "extensions_latest.txt") -Encoding utf8 -Force

# 4. 환경 정보 저장
$envInfo = @{
    ExportDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Computer = $env:COMPUTERNAME
    User = $env:USERNAME
    VSCodeVersion = (& code --version 2>$null | Select-Object -First 1)
    NodeVersion = (& node --version 2>$null)
    PythonVersion = (& python --version 2>$null)
    UvVersion = (& uv --version 2>$null)
    ExtensionCount = $extensions.Count
}
$envInfo | ConvertTo-Json | Out-File (Join-Path $outputDir "environment_$timestamp.json") -Encoding utf8
Write-Host "✅ 환경 정보 → environment_$timestamp.json" -ForegroundColor Green

Write-Host "`n"+"="*50 -ForegroundColor Cyan
Write-Host "📁 내보내기 완료: $outputDir" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan
