<!--
Project-specific Copilot instructions for python-email (court-evidence-system).
Keep this file short, actionable and focused on discoverable repository patterns.
-->
# AI Coding Assistant Instructions — python-email

목적: 이 파일은 AI 코딩 에이전트가 이 저장소에서 즉시 생산적으로 일하도록 돕는 핵심 정보만 담습니다.

## 빠른 요약
- 언어: Python 3.13.9, 웹 프레임워크: Flask 3.x
- 주요 디렉터리: `src/web`, `src/mail_parser`, `src/core`, `src/evidence`, `templates`, `static`, `scripts`, `tests`
- 엔트리포인트: `src/web/app.py:create_app()` — 여러 runner와 system tests가 동일한 앱 팩토리를 사용합니다.

## 아키텍처(핵심)
- 앱은 앱 팩토리 패턴(`create_app(config_path: str = None)`)으로 구성되어 있습니다. 예: `src/web/app.py`.
- 서버 실행은 runner 스크립트에서 이루어집니다: `src/runner/run_server.py`, `src/runner/start_web.py` — 이들은 내부에서 `create_app()`을 호출합니다.
- 메일 파싱과 증거 관리는 `src/mail_parser`와 `src/evidence`에 집중되어 있으며, 검증·타임라인 로직은 `src/timeline`에 있습니다.

## 핵심 워크플로우(명령 예시)
- 가상환경 및 의존성 설치:
```bash
python -m venv .venv
source .venv/bin/activate   # 윈도우 PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```
- 테스트 실행 (단위/통합):
```bash
python -m pytest -q   # 또는 특정 파일: python -m pytest tests/ 또는 test_api_collection.py
```
- 개발 서버(로컬) 실행 예시:
```bash
python src/runner/run_server.py    # 또는: python -m src.runner.run_server (루트에서)
```

## 프로젝트 규칙 / 컨벤션 (특이사항)
- 커밋 메시지 포맷: `YYYY-MM-DD HH:mm:ss_메시지` (레포 정책에 맞춰 커밋하세요).
- 정적 자산: `static/` 및 `templates/` 사용 — 프로젝트는 다크모드와 Font Awesome 통합을 적용했습니다(참고: `static/css/`).
- 앱은 앱 팩토리를 통해 구성 파일을 주입하므로, 변경 시 `create_app()` 호출부(예: `src/runner/*`, `src/system_tests/*`)를 같이 점검하세요.

## 코드 패턴/예시(검색시점)
- 앱 팩토리 정의: [src/web/app.py](src/web/app.py#L12-L20) (검색: `def create_app`)
- runner에서 앱 사용: [src/runner/run_server.py](src/runner/run_server.py#L1-L60)
- 시스템/통합 테스트도 `create_app()`을 사용해 앱 컨텍스트를 만듭니다. (see `src/system_tests/core_tests.py`)

## 통합 포인트 / 외부 도구
- Codacy, Serena 등의 MCP 도구와 연계되어 있습니다. 변경 후 자동 품질분석 규칙이 있으니 아래를 따르세요.

## 수정 규칙(중요)
- 이 저장소의 `.github/codacy.instructions.md` 규칙을 따르세요: 파일을 편집한 직후 Codacy CLI 분석(또는 팀이 지정한 MCP 작업)을 실행해 결과를 확인해야 합니다.
- 의존성(requirements.txt) 변경을 포함한 패키지 작업 뒤에는 보안 스캔(`trivy`) 실행 요구가 있습니다 — 보안 이슈가 나오면 우선 해결하세요.

## 요약 체크리스트 (AI가 자동 수정할 때)
- 변경 범위를 최소화하세요 (심볼 단위 수정 권장).
- `create_app()` 호출 위치들을 확인하고 필요한 경우 함께 업데이트하세요.
- 테스트(관련 파일 또는 전체)를 실행해 변경 영향도를 검증하세요.
- 수정 후 Codacy 분석을 실행하고 결과를 반영하세요.

---
피드백: 이 파일의 어떤 부분을 더 상세히 채우길 원하나요? (예: 특정 런타임 설정, 환경변수 목록, 더 많은 파일 링크)
