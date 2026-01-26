<#
Setup VS Code globally for WSL + Docker + Codacy usage.
Run this script in an elevated PowerShell on Windows to install recommended
extensions and modify your user-level VS Code `settings.json` and `tasks.json`.

Usage: Open PowerShell (not WSL) and run:
  .\tools\setup_vscode_global.ps1

The script will:
- install recommended extensions (Remote - WSL, Docker, Codacy helper)
- set default integrated terminal to WSL
- add a user task `Codacy: Analyze (WSL)` that runs the repository script via WSL
- optionally trigger WSL-side Codacy convenience script setup
#>

param(
    [switch]$RunWSLSetup
)

function Ensure-CodeCli {
    if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
        Write-Error "VS Code CLI 'code' not found in PATH. Install 'code' command from VS Code (Command Palette: 'Shell Command: Install 'code' command in PATH')."
        exit 1
    }
}

function Install-Extensions {
    $exts = @(
        'ms-vscode-remote.remote-wsl',
        'ms-azuretools.vscode-docker',
        'ms-azuretools.vscode-containers',
        'codacy-app.codacy'
    )
    foreach ($e in $exts) {
        Write-Host "Installing extension: $e"
        code --install-extension $e --force | Out-Null
    }
}

function Update-UserSettings {
    $appdata = $env:APPDATA
    if (-not $appdata) { Write-Error "APPDATA not found"; return }
    $settingsPath = Join-Path $appdata 'Code\User\settings.json'
    $settings = @{ }
    if (Test-Path $settingsPath) {
        $raw = Get-Content $settingsPath -Raw -ErrorAction SilentlyContinue
        if ($raw) { $settings = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue }
    }
    # Set WSL as default integrated terminal on Windows
    $settings.'terminal.integrated.profiles.windows' = @{ 'WSL Bash' = @{ path = 'C:\\Windows\\System32\\wsl.exe'; args = @() } }
    $settings.'terminal.integrated.defaultProfile.windows' = 'WSL Bash'
    $settings.'terminal.integrated.shell.windows' = 'C:\\Windows\\System32\\wsl.exe'

    $json = $settings | ConvertTo-Json -Depth 10
    $json | Set-Content -Path $settingsPath -Encoding UTF8
    Write-Host "Updated user settings: $settingsPath"
}

function Update-UserTasks {
    $appdata = $env:APPDATA
    $tasksPath = Join-Path $appdata 'Code\User\tasks.json'
    $tasks = @{ version = '2.0.0'; tasks = @() }
    if (Test-Path $tasksPath) {
        $raw = Get-Content $tasksPath -Raw -ErrorAction SilentlyContinue
        if ($raw) { $tasks = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue }
    }
    $codacyTask = @{
        label = 'Codacy: Analyze (WSL)'
        type = 'shell'
        command = "wsl -d Ubuntu -- bash -lc 'cd /mnt/c/dev/python-email && ./tools/codacy_run.sh'"
        presentation = @{ reveal = 'always'; panel = 'shared' }
        problemMatcher = @()
    }
    # remove any existing Codacy task and add ours
    $tasks.tasks = ($tasks.tasks | Where-Object { $_.label -ne 'Codacy: Analyze (WSL)' }) + ,$codacyTask

    $tasks | ConvertTo-Json -Depth 10 | Set-Content -Path $tasksPath -Encoding UTF8
    Write-Host "Updated user tasks: $tasksPath"
}

function Ask-YesNo($msg) {
    $r = Read-Host "$msg (y/n)"
    return $r -match '^[Yy]'
}

Ensure-CodeCli
Install-Extensions
Update-UserSettings
Update-UserTasks

if ($RunWSLSetup -or (Ask-YesNo 'Would you like to run the WSL Codacy convenience installer now?')) {
    if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
        Write-Error 'wsl command not available from PowerShell environment.'; exit 1
    }
    Write-Host 'Invoking WSL setup script (tools/setup_codacy_wsl.sh) inside WSL...'
    wsl -d Ubuntu -- bash -lc 'cd /mnt/c/dev/python-email && bash ./tools/setup_codacy_wsl.sh'
}

Write-Host 'Global VS Code setup complete. Restart VS Code to apply changes.'
