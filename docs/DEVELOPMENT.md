# 개발 가이드 (간단)

이 문서는 로컬 개발 환경에서 이 레포지토리(mail_parser)를 빠르게 기동하고, 변경사항을 검증하며, Codacy 정적분석을 실행하는 방법을 정리합니다. Windows 환경에서는 Codacy CLI 실행이 제한적일 수 있으므로 WSL에서 실행하거나 CI(GitHub Actions 등)에 분석 작업을 두는 것을 권장합니다.

## 사전 준비

- Python 3.10+ 설치

- 가상환경 생성 및 의존성 설치

```powershell
# 저장소 루트에서
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 개발 서버 (Full UI 개발용)

- 개발 중에는 레거시(full UI) 팩토리를 기본으로 사용하도록 `run_server.py`가 동작합니다. 호환성/경량 팩토리가 필요하면 환경변수를 이용하거나, 명령 인자로 설정할 수 있습니다.

예시: 개발 서버 실행

```powershell
python run_server.py --dev --port 5000
# 또는

# 개발 가이드 (간단)

이 문서는 로컬 개발 환경에서 이 레포지토리(mail_parser)를 빠르게 기동하고, 변경사항을 검증하며, Codacy 정적분석을 실행하는 방법을 정리합니다. Windows 환경에서는 Codacy CLI 실행이 제한적일 수 있으므로 WSL에서 실행하거나 CI(GitHub Actions 등)에 분석 작업을 두는 것을 권장합니다.

## 사전 준비

- Python 3.10+ 설치

- 가상환경 생성 및 의존성 설치

```powershell
# 저장소 루트에서
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 개발 서버 (Full UI 개발용)

- 개발 중에는 레거시(full UI) 팩토리를 기본으로 사용하도록 `run_server.py`가 동작합니다. 호환성/경량 팩토리가 필요하면 환경변수를 이용하거나, 명령 인자로 설정할 수 있습니다.

예시: 개발 서버 실행

```powershell
python run_server.py --dev --port 5000
# 또는
python main.py --web --port 5000
```

환경변수(선택)

- `USE_MINIMAL_UI=1` : 최소 UI(호환성) 팩토리를 사용합니다。

## 빠른 점검(라우트 확인)

- `/upload` 같은 핵심 라우트가 등록되어 있는지 확인하려면 제공된 스크립트를 사용하세요。

```powershell
.\.venv\Scripts\python.exe .\scripts\check_upload_route.py
```

스크립트는 프로젝트 루트를 자동 감지하고, DB 연결 및 라우트 등록 여부를 출력합니다。

## 단위 테스트 실행 (빠른 회귀)

- 느린 통합 테스트는 제외하고 빠른 테스트만 돌려 개발 속도를 유지하세요。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ui_routes.py -q
```

## 브라우저에서 동작 확인

1. 서버를 기동한 뒤 브라우저에서 `http://localhost:5000/upload`로 접속합니다。
2. 실제 mbox 파일을 업로드해 진행률 표시 및 서버 응답(리다이렉트)을 확인하세요。

## Codacy 정적분석 (권장: WSL 또는 CI에서 수행)

Windows 네이티브 환경에서는 Codacy 분석 도구가 제한적으로 동작할 수 있습니다. 아래 두 가지 방법을 권장합니다。

### WSL(로컬)에서 실행 (권장 개발자용)

- WSL(Windows Subsystem for Linux)을 설치하세요(설치 가이드: <https://learn.microsoft.com/windows/wsl/install>)。

- WSL 터미널을 열고 저장소를 마운트한 디렉터리(또는 복사본)를 사용해 아래를 실행하세요。

```bash
# WSL에서
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Codacy CLI는 Codacy 문서를 따라 설치합니다。 (Codacy 공식 가이드 참고)
# 예: curl -sL https://.../codacy-cli -o codacy && chmod +x codacy && ./codacy analyze ...
```

- 로컬에서 Codacy CLI를 바로 쓰기 어렵다면 CI 기반 분석으로 대체하세요(아래 참고)。

### GitHub Actions (CI)에서 Codacy 자동화 (권장: PR마다 실행)

- 저장소에 `.github/workflows/codacy-analysis.yml` 워크플로를 추가했습니다。PR에 대해 자동으로 분석을 수행하도록 구성되어 있습니다。조직에서 Codacy 연동 방식(토큰、플러그인 등)에 따라 `CODACY_PROJECT_TOKEN` 시크릿을 설정하세요。

## 변경 후 체크리스트

- 서버를 재기동하고 `/upload`가 브라우저에서 작동하는지 확인합니다。

- 변경된 파일이 있을 때는 간단한 테스트를 실행해 회귀가 없는지 확인합니다。

- Codacy에서 오류가 나오면 문서와 코드 스타일을 맞춰 수정하고 재분석합니다。

---

필요하면 이 문서를 더 세부적으로(예: WSL에서 Codacy CLI 설치 명령、GitHub Actions 완전 예시) 확장해 드리겠습니다。

```powershell
.\.venv\Scripts\python.exe .\scripts\check_upload_route.py
```

스크립트는 프로젝트 루트를 자동 감지하고, DB 연결 및 라우트 등록 여부를 출력합니다.

## 단위 테스트 실행 (빠른 회귀)

- 느린 통합 테스트는 제외하고 빠른 테스트만 돌려 개발 속도를 유지하세요.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ui_routes.py -q
```

## 브라우저에서 동작 확인

1. 서버를 기동한 뒤 브라우저에서 `http://localhost:5000/upload`로 접속합니다.
2. 실제 mbox 파일을 업로드해 진행률 표시 및 서버 응답(리다이렉트)을 확인하세요.

## Codacy 정적분석 (권장: WSL 또는 CI에서 수행)

Windows 네이티브 환경에서는 Codacy 분석 도구가 제한적으로 동작할 수 있습니다. 아래 두 가지 방법을 권장합니다.

### WSL(로컬)에서 실행 (권장 개발자용)

- WSL(Windows Subsystem for Linux)을 설치하세요(설치 가이드: <https://learn.microsoft.com/windows/wsl/install>).

- WSL 터미널을 열고 저장소를 마운트한 디렉터리(또는 복사본)를 사용해 아래를 실행하세요.

```bash
# WSL에서
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Codacy CLI는 Codacy 문서를 따라 설치합니다. (Codacy 공식 가이드 참고)
# 예: curl -sL https://.../codacy-cli -o codacy && chmod +x codacy && ./codacy analyze ...
```

- 로컬에서 Codacy CLI를 바로 쓰기 어렵다면 CI 기반 분석으로 대체하세요(아래 참고).

### GitHub Actions (CI)에서 Codacy 자동화 (권장: PR마다 실행)

- 저장소에 [`.github/workflows/codacy-analysis.yml`](../.github/workflows/codacy-analysis.yml) 워크플로를 추가했습니다. PR에 대해 자동으로 분석을 수행하도록 구성되어 있습니다. 조직에서 Codacy 연동 방식(토큰, 플러그인 등)에 따라 `CODACY_PROJECT_TOKEN` 시크릿을 설정하세요.

## 변경 후 체크리스트

- 서버를 재기동하고 `/upload`가 브라우저에서 작동하는지 확인합니다.

- 변경된 파일이 있을 때는 간단한 테스트를 실행해 회귀가 없는지 확인합니다.

- Codacy에서 오류가 나오면 문서와 코드 스타일을 맞춰 수정하고 재분석합니다.

---

필요하면 이 문서를 더 세부적으로(예: WSL에서 Codacy CLI 설치 명령, GitHub Actions 완전 예시) 확장해 드리겠습니다.
