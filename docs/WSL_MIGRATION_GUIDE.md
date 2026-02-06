# WSL Ubuntu → C:\wsl 이동 가이드

## 현재 상황
- **현재 위치**: `C:\Users\cross\AppData\Local\wsl\{a7661f92-5853-4e7c-8922-cae2aec482c7}`
- **ext4.vhdx 크기**: 27.59 GB
- **남은 디스크 공간**: ~24 GB

⚠️ **중요**: 백업 export 시 추가로 ~28GB가 필요합니다. 현재 공간이 부족합니다!

---

## 옵션 1: 외부 드라이브 사용 (권장)

외부 USB 드라이브나 D: 드라이브가 있다면:

```powershell
# 관리자 PowerShell에서 실행
wsl --shutdown
wsl --export Ubuntu D:\wsl-backup\Ubuntu.tar
wsl --unregister Ubuntu
wsl --import Ubuntu C:\wsl\Ubuntu D:\wsl-backup\Ubuntu.tar --version 2
```

---

## 옵션 2: 직접 이동 (공간 절약 방식)

WSL을 종료하고 vhdx 파일을 직접 이동 후 레지스트리 수정:

### Step 1: WSL 종료
```powershell
wsl --shutdown
```

### Step 2: 폴더 생성 및 파일 이동
```powershell
# 관리자 PowerShell
mkdir C:\wsl\Ubuntu -Force
Move-Item "C:\Users\cross\AppData\Local\wsl\{a7661f92-5853-4e7c-8922-cae2aec482c7}\*" "C:\wsl\Ubuntu\"
```

### Step 3: 레지스트리 수정
```powershell
# 레지스트리 경로 업데이트
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\{a7661f92-5853-4e7c-8922-cae2aec482c7}"
Set-ItemProperty -Path $regPath -Name "BasePath" -Value "C:\wsl\Ubuntu"
```

### Step 4: 확인
```powershell
wsl --list -v
wsl -d Ubuntu
```

---

## 옵션 3: 불필요 파일 정리 후 export (현재 권장)

### 먼저 WSL 내부 정리:
```bash
# WSL 내부에서
sudo apt clean
sudo apt autoremove -y
rm -rf ~/.cache/*
```

### vhdx 압축:
```powershell
wsl --shutdown
# Hyper-V 관리자 또는 diskpart로 vhdx 압축
```

---

## Windows Defender 제외 설정

이동 후 반드시 설정:

```powershell
# 관리자 PowerShell
Add-MpPreference -ExclusionPath "C:\wsl"
Add-MpPreference -ExclusionPath "\\wsl$"
Add-MpPreference -ExclusionPath "\\wsl.localhost"
Add-MpPreference -ExclusionProcess "wsl.exe"
Add-MpPreference -ExclusionProcess "wslhost.exe"
```

---

## 기본 사용자 설정 (import 후)

```bash
# /etc/wsl.conf 설정
sudo tee /etc/wsl.conf << 'EOF'
[user]
default=crossman

[interop]
appendWindowsPath=true

[automount]
enabled=true
options="metadata,umask=22,fmask=11"
EOF
```

```powershell
wsl --shutdown
```

---

작성일: 2026-02-02
