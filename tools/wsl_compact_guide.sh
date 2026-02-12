#!/usr/bin/env bash
set -euo pipefail
# =============================================================================
# WSL VHDX 압축 스크립트
# 목적: WSL에서 데이터 삭제 후에도 C: 드라이브의 ext4.vhdx가 줄지 않으므로
#       수동으로 압축하여 C: 드라이브 공간을 회수
#
# 사용 순서:
#   1. WSL 내부에서 먼저 정리: bash tools/docker_optimize.sh clean
#   2. WSL 종료: wsl.exe --shutdown
#   3. Windows PowerShell(관리자)에서 이 스크립트의 안내를 따름
# =============================================================================

echo "========================================="
echo "  WSL VHDX 압축 가이드"
echo "========================================="
echo ""
echo "현재 WSL 디스크 사용량:"
df -h / | grep -E "Filesystem|/"
echo ""
echo "C: 드라이브 여유 공간:"
df -h /mnt/c | grep -E "Filesystem|/mnt/c"
echo ""

echo "─── 순서 ────────────────────────────────"
echo ""
echo "1단계: WSL 내부 정리 (이미 완료되었으면 건너뜀)"
echo "   bash tools/docker_optimize.sh clean"
echo ""
echo "2단계: Windows PowerShell(관리자)에서 실행:"
echo ""
echo '   wsl.exe --shutdown'
echo ""
echo '   # VHDX 파일 위치 확인 (관리자 PowerShell):'
echo '   Get-ChildItem -Path "C:\Users\cross" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue | Select-Object FullName, @{N="SizeMB";E={[math]::Round($_.Length/1MB)}}'
echo ""
echo '   # VHDX 압축 (diskpart 사용):'
echo '   # === diskpart 명령 (아래를 순서대로 입력) ==='
echo '   diskpart'
echo '   select vdisk file="<위에서 찾은 ext4.vhdx 경로>"'
echo '   compact vdisk'
echo '   exit'
echo ""
echo '   # 또는 Optimize-VHD 사용 (Hyper-V 기능 필요):'
echo '   Optimize-VHD -Path "<ext4.vhdx 경로>" -Mode Full'
echo ""
echo "3단계: WSL 재시작"
echo '   wsl.exe'
echo ""
echo "─── .wslconfig 메모리 제한 설정 ─────────"
echo ""
echo "C:\\Users\\cross\\.wslconfig 파일 생성/편집:"
echo ""
echo "[wsl2]"
echo "memory=4GB"
echo "swap=2GB"
echo "localhostForwarding=true"
echo ""
echo "이 설정으로 WSL이 메모리를 과도하게 사용하는 것을 방지합니다."
echo "========================================="
