<!--
Project-specific Copilot instructions for python-email (court-evidence-system).
Keep this file short, actionable and focused on discoverable repository patterns.
-->
# AI Coding Assistant Instructions — python-email

## 🚨 토큰 최적화 (최우선 규칙)
- **응답은 최대한 짧게**. 불필요한 설명 금지.
- 코드 변경 시 **변경된 부분만** 출력.
- 표, 리스트는 **3줄 이하**로 요약.
- "~하겠습니다", "~드리겠습니다" 등 **경어체 인사말 생략**.
- 요청받지 않은 추가 제안/개선사항 제시 금지.
- 도구 실행 결과는 **핵심만 1-2줄로 요약**.

## ⚠️ 세션 관리 (불변 규칙)
> 토큰 관리 실패 = 협업 시간 감소. 이 규칙은 어디서든 적용.

- 토큰 **20% 도달** → 즉시 새 채팅 시작
- 대화 **10턴 초과** → 새 채팅 시작
- 주제 변경 시 → 새 채팅 시작
- 세션 시작 시: 필요한 파일만 `@file:` 지정, "설명 없이" 명시

---

목적: 이 파일은 AI 코딩 에이전트가 이 저장소에서 즉시 생산적으로 일하도록 돕는 핵심 정보만 담습니다.

## 빠른 요약
- 언어: Python 3.12 (WSL), 웹 프레임워크: Flask 3.x
- 개발환경: **WSL Ubuntu** (터미널, MCP, Node/npm 모두 WSL)
- 주요 디렉터리: `src/web`, `src/mail_parser`, `src/core`, `src/evidence`, `templates`, `static`, `scripts`, `tests`
- 엔트리포인트: `src/web/app.py:create_app()`

## 환경 구축 (새 머신/클론 시)
1. `git clone` → `.vscode/` 설정 자동 적용
2. `bash tools/setup_wsl_env.sh` → WSL 의존성 전체 설치
3. `.vscode/.env`에 API 키 설정 (`.env.example` 참조)
4. VS Code Settings Sync 활성화 → 사용자 설정 동기화

## 아키텍처(핵심)
- 앱은 앱 팩토리 패턴(`create_app(config_path: str = None)`)으로 구성되어 있습니다. 예: `src/web/app.py`.
- 서버 실행은 runner 스크립트에서 이루어집니다: `src/runner/run_server.py`, `src/runner/start_web.py` — 이들은 내부에서 `create_app()`을 호출합니다.
- 메일 파싱과 증거 관리는 `src/mail_parser`와 `src/evidence`에 집중되어 있으며, 검증·타임라인 로직은 `src/timeline`에 있습니다.

## 핵심 워크플로우(WSL)
```bash
bash tools/setup_wsl_env.sh        # 최초 환경 구축
source .venv/bin/activate           # venv 활성화
pip install -r requirements.txt     # 의존성
python -m pytest -q                 # 테스트
python src/runner/run_server.py     # 개발 서버
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
