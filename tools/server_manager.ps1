# 웹서버 관리 스크립트
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('start', 'stop', 'restart', 'status', 'test')]
  [string]$Action
)

$ErrorActionPreference = "Stop"
$ServerPort = 5000
$ProjectRoot = "c:\dev\python-email"

function Get-ServerProcess {
  Get-Process python -ErrorAction SilentlyContinue |
  Where-Object {
    $_.WorkingSet -gt 10MB -and
    $_.CommandLine -like "*src.web.app*"
  }
}

function Stop-Server {
  Write-Host "🛑 서버 중지 중..." -ForegroundColor Yellow
  $processes = Get-ServerProcess
  if ($processes) {
    $processes | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "✅ 서버 중지 완료" -ForegroundColor Green
  }
  else {
    Write-Host "ℹ️ 실행 중인 서버 없음" -ForegroundColor Gray
  }
}

function Start-Server {
  Write-Host "🚀 서버 시작 중..." -ForegroundColor Cyan

  # 기존 프로세스 정리
  Stop-Server

  # 백그라운드로 서버 시작
  Push-Location $ProjectRoot
  $job = Start-Job -ScriptBlock {
    param($root)
    Set-Location $root
    python -m src.web.app 2>&1
  } -ArgumentList $ProjectRoot
  Pop-Location

  # 서버 시작 대기 (최대 15초)
  Write-Host "⏳ 서버 준비 중..." -ForegroundColor Gray
  $maxWait = 15
  $waited = 0
  $ready = $false

  while ($waited -lt $maxWait -and -not $ready) {
    Start-Sleep -Seconds 1
    $waited++

    try {
      $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort/health" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
      if ($response.StatusCode -eq 200) {
        $ready = $true
      }
    }
    catch {
      # 계속 대기
    }

    if ($waited % 3 -eq 0) {
      Write-Host "  ⏱️ $waited 초 경과..." -ForegroundColor Gray
    }
  }

  if ($ready) {
    Write-Host "✅ 서버 시작 완료 (http://localhost:$ServerPort)" -ForegroundColor Green
    return $true
  }
  else {
    Write-Host "❌ 서버 시작 실패 (타임아웃)" -ForegroundColor Red
    Write-Host "Job 출력:" -ForegroundColor Yellow
    Receive-Job -Job $job | Select-Object -First 20
    return $false
  }
}

function Get-ServerStatus {
  $process = Get-ServerProcess
  if ($process) {
    Write-Host "✅ 서버 실행 중" -ForegroundColor Green
    Write-Host "  PID: $($process.Id)" -ForegroundColor Gray
    Write-Host "  메모리: $([math]::Round($process.WorkingSet/1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "  실행 시간: $((Get-Date) - $process.StartTime)" -ForegroundColor Gray
    return $true
  }
  else {
    Write-Host "❌ 서버 실행 안 됨" -ForegroundColor Red
    return $false
  }
}

function Test-Server {
  param([string[]]$Endpoints)

  Write-Host "`n=== 서버 테스트 ===" -ForegroundColor Cyan

  $passCount = 0
  $totalCount = $Endpoints.Count

  foreach ($endpoint in $Endpoints) {
    try {
      $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort$endpoint" -Method GET -TimeoutSec 5 -UseBasicParsing
      $status = $response.StatusCode
      if ($status -eq 200) {
        $passCount++
        Write-Host "✓ $endpoint : $status" -ForegroundColor Green
      }
      else {
        Write-Host "✗ $endpoint : $status" -ForegroundColor Yellow
      }
    }
    catch {
      $status = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "ERROR" }
      Write-Host "✗ $endpoint : $status" -ForegroundColor Red
    }
  }

  Write-Host "`n결과: $passCount/$totalCount 통과" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })
  return $passCount -eq $totalCount
}

# 액션 실행
switch ($Action) {
  'start' {
    Start-Server
  }
  'stop' {
    Stop-Server
  }
  'restart' {
    Start-Server
  }
  'status' {
    Get-ServerStatus
  }
  'test' {
    # 기본 테스트 엔드포인트
    $testEndpoints = @('/health', '/timeline', '/integrated_timeline')
    Test-Server -Endpoints $testEndpoints
  }
}
