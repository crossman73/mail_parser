<#
.SYNOPSIS
    VS Code 확장 프로그램 자동 설치 스크립트
.DESCRIPTION
    mail_parser 프로젝트에 필요한 모든 VS Code 확장 프로그램을 설치합니다.
.EXAMPLE
    .\setup_vscode_extensions.ps1
    .\setup_vscode_extensions.ps1 -CoreOnly
#>

param(
    [switch]$CoreOnly,      # 필수 확장만 설치
    [switch]$SkipInstalled, # 이미 설치된 확장 건너뛰기
    [switch]$List           # 설치할 확장 목록만 표시
)

# 확장 프로그램 정의
$coreExtensions = @(
    # GitHub Copilot
    "github.copilot",
    "github.copilot-chat",
    
    # Python 필수
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    
    # 코드 품질
    "codacy-app.codacy"
)

$pythonExtensions = @(
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.autopep8",
    "donjayamanne.python-extension-pack",
    "donjayamanne.python-environment-manager",
    "kevinrose.vsc-python-indent",
    "mgesbert.python-path",
    "njpwerner.autodocstring",
    "tushortz.python-extended-snippets"
)

$webExtensions = @(
    "ecmel.vscode-html-css",
    "pranaygp.vscode-css-peek",
    "zignd.html-css-class-completion",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "christian-kohler.npm-intellisense",
    "batisteo.vscode-django",
    "wholroyd.jinja"
)

$gitExtensions = @(
    "github.vscode-pull-request-github",
    "github.vscode-github-actions",
    "github.github-vscode-theme"
)

$containerExtensions = @(
    "ms-azuretools.vscode-docker",
    "ms-azuretools.vscode-containers",
    "ms-vscode-remote.remote-containers",
    "ms-vscode-remote.remote-ssh",
    "ms-vscode-remote.remote-ssh-edit",
    "ms-vscode-remote.remote-wsl",
    "ms-vscode-remote.vscode-remote-extensionpack",
    "ms-vscode.remote-explorer",
    "ms-vscode.remote-server"
)

$productivityExtensions = @(
    "aaron-bond.better-comments",
    "usernamehw.errorlens",
    "wayou.vscode-todo-highlight",
    "humao.rest-client",
    "rangav.vscode-thunder-client",
    "amatiasq.sort-imports",
    "eriklynd.json-tools",
    "mariusalchimavicius.json-to-ts",
    "mechatroner.rainbow-csv",
    "mikestead.dotenv",
    "redhat.vscode-yaml",
    "alefragnani.project-manager"
)

$markdownExtensions = @(
    "yzhang.markdown-all-in-one",
    "davidanson.vscode-markdownlint",
    "shd101wyy.markdown-preview-enhanced",
    "bierner.markdown-mermaid"
)

$themeExtensions = @(
    "azemoh.one-monokai",
    "pkief.material-icon-theme",
    "naumovs.color-highlight"
)

$koreanExtensions = @(
    "ms-ceintl.vscode-language-pack-ko",
    "dinner.korean-translator",
    "yunseok.korean-spell-checker-vs-code"
)

$otherExtensions = @(
    "ms-vscode.powershell",
    "foxundermoon.shell-format",
    "timonwong.shellcheck",
    "ms-vscode.makefile-tools",
    "ms-vscode.live-server",
    "ms-vscode.notepadplusplus-keybindings",
    "ms-vscode.vscode-typescript-next",
    "streetsidesoftware.code-spell-checker",
    "github.codespaces",
    "google.geminicodeassist",
    "semanticworkbenchteam.mcp-server-vscode",
    "vscjava.vscode-java-upgrade"
)

# 설치할 확장 목록 결정
if ($CoreOnly) {
    $allExtensions = $coreExtensions
    Write-Host "📦 필수 확장만 설치합니다 ($($allExtensions.Count)개)" -ForegroundColor Cyan
} else {
    $allExtensions = $coreExtensions + $pythonExtensions + $webExtensions + $gitExtensions + 
                     $containerExtensions + $productivityExtensions + $markdownExtensions + 
                     $themeExtensions + $koreanExtensions + $otherExtensions
    Write-Host "📦 전체 확장을 설치합니다 ($($allExtensions.Count)개)" -ForegroundColor Cyan
}

# 목록만 표시
if ($List) {
    Write-Host "`n설치할 확장 프로그램 목록:" -ForegroundColor Yellow
    $allExtensions | ForEach-Object { Write-Host "  - $_" }
    exit 0
}

# 이미 설치된 확장 확인
$installedExtensions = @()
if ($SkipInstalled) {
    Write-Host "`n🔍 설치된 확장 확인 중..." -ForegroundColor Yellow
    $installedExtensions = & code --list-extensions 2>$null
}

# 설치 진행
$installed = 0
$skipped = 0
$failed = 0

Write-Host "`n🚀 확장 프로그램 설치 시작...`n" -ForegroundColor Green

foreach ($ext in $allExtensions) {
    if ($SkipInstalled -and $installedExtensions -contains $ext) {
        Write-Host "⏭️  $ext (이미 설치됨)" -ForegroundColor DarkGray
        $skipped++
        continue
    }
    
    Write-Host "📥 설치 중: $ext" -ForegroundColor White
    $result = & code --install-extension $ext --force 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 완료" -ForegroundColor Green
        $installed++
    } else {
        Write-Host "   ❌ 실패: $result" -ForegroundColor Red
        $failed++
    }
}

# 결과 요약
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "📊 설치 결과 요약" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan
Write-Host "   ✅ 설치 완료: $installed" -ForegroundColor Green
Write-Host "   ⏭️  건너뜀:    $skipped" -ForegroundColor Yellow
Write-Host "   ❌ 실패:      $failed" -ForegroundColor Red
Write-Host "="*50 -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host "`n⚠️  일부 확장 설치에 실패했습니다. VS Code를 재시작 후 다시 시도해주세요." -ForegroundColor Yellow
}

Write-Host "`n✨ VS Code를 재시작하면 모든 확장이 활성화됩니다." -ForegroundColor Green
