<#
tools/cleanup_storage.ps1
Windows용 안전한 디스크 정리 보조 스크립트
기본: 드라이런. 실제 삭제/정리하려면 -Yes 스위치 사용.
#>

param(
    [switch]$Yes,
    [switch]$RemoveLargeFiles,
    [string]$JsonOut = '',
    [string]$GenerateDeleteList = '',
    [string]$SelectDeleteList = ''
)

function Show-Usage {
    @'
Usage: cleanup_storage.ps1 [-Yes] [-RemoveLargeFiles] [-JsonOut <path>] [-GenerateDeleteList <path>] [-SelectDeleteList <path>]

Options:
  -Yes                   : 실제 삭제/정리 수행 (없으면 드라이런)
  -RemoveLargeFiles      : 탐지된 큰 파일을 삭제 (권장하지 않음)
  -JsonOut <path>        : JSON 형식 리포트 파일 경로
  -GenerateDeleteList <path> : CSV 형식 삭제 후보 목록 생성
  -SelectDeleteList <path>   : 생성된 목록을 기반으로 대화형 삭제

Note: 관리자 권한이 필요할 수 있습니다. 중요 데이터는 백업하세요.
'@
}

if ($PSBoundParameters['Help']) { Show-Usage; exit }

Write-Output "[cleanup_storage.ps1] mode: $(if ($Yes) { 'EXECUTE' } else { 'DRY-RUN' })"

Write-Output "\n[1/4] Drive usage (C:)"
$drive = Get-PSDrive -Name C | Select-Object Name, @{Name='UsedGB';Expression={[math]::round(($_.Used/1GB),2)}}, @{Name='FreeGB';Expression={[math]::round(($_.Free/1GB),2)}}
$drive | Format-Table -AutoSize

Write-Output "\n[2/4] Top directories in user profile (one level)"
$home = $env:USERPROFILE
$topdirs = Get-ChildItem -Path $home -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $size = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{ Path = $_.FullName; SizeMB = if ($size) { [math]::Round($size/1MB,2) } else { 0 } }
} | Sort-Object SizeMB -Descending | Select-Object -First 30
$topdirs | Format-Table -AutoSize

Write-Output "\n[3/4] Top 50 large files on C: (this can be slow)"
if (-not $Yes) {
    Write-Output "DRY-RUN: to speed up, run with -Yes to allow full scan or use WinDirStat."
}
try {
    if ($Yes) {
        $largest = Get-ChildItem -Path C:\ -Recurse -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object FullName,@{Name='MB';Expression={[math]::Round($_.Length/1MB,2)}} -First 50
        $largest | Format-Table -AutoSize
    } else {
        Write-Output "Skipping full file scan (use -Yes to run it)."
    }
} catch {
    Write-Output "Error during file scan: $_"
}

if ($RemoveLargeFiles -and $Yes) {
    Write-Output "\n[4/4] Removing selected large files (requested)"
    Write-Output "This is destructive. You must edit the script to select files for removal or pipe input."
    Write-Output "No automatic deletion performed by default."
}

if ($JsonOut) {
    $report = [PSCustomObject]@{
        timestamp = (Get-Date).ToString('o')
        drive = $drive
        top_dirs = $topdirs
        largest_files = if ($largest) { $largest } else { @() }
        note = 'run with -Yes to perform destructive actions'
    }
    $report | ConvertTo-Json -Depth 5 | Out-File -FilePath $JsonOut -Encoding UTF8
    Write-Output "Wrote JSON report to $JsonOut"
}

if ($GenerateDeleteList) {
    $items = @()
    foreach ($d in $topdirs) { $items += [PSCustomObject]@{ Path = $d.Path; SizeMB = $d.SizeMB } }
    $items | Export-Csv -NoTypeInformation -Path $GenerateDeleteList -Encoding UTF8
    Write-Output "Generated delete list at $GenerateDeleteList"
}

if ($SelectDeleteList) {
    if (-not (Test-Path $SelectDeleteList)) { Write-Output "Select delete list not found: $SelectDeleteList"; exit 1 }
    $list = Import-Csv -Path $SelectDeleteList
    if (-not $Yes) { Write-Output "DRY-RUN: will not delete. Re-run with -Yes to execute." }
    foreach ($item in $list) {
        Write-Output "Candidate: $($item.Path) ($($item.SizeMB) MB)"
        if ($Yes) {
            $confirm = Read-Host "Type YES to delete"
            if ($confirm -eq 'YES') {
                Remove-Item -LiteralPath $item.Path -Recurse -Force -ErrorAction SilentlyContinue
                Write-Output "Deleted $($item.Path)"
            } else { Write-Output "Skipped $($item.Path)" }
        }
    }
}

Write-Output "\nDefender exclusion guidance: run PowerShell as Administrator and add exclusion for WSL distro path or specific project node_modules."
Write-Output "Example (PowerShell admin): Add-MpPreference -ExclusionPath 'C:\Users\<USER>\AppData\Local\Packages\CanonicalGroupLimited*'"
Write-Output "For UNC path: Add-MpPreference -ExclusionPath '\\wsl$\Ubuntu\home\<user>\projects\myapp\node_modules'"

Write-Output "\nDone. Review outputs and run with -Yes only when ready."
