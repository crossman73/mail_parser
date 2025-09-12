## 요약 — 이 레포에서 에이전트가 우선 알면 좋은 것

- 목적: 이메일(.eml / mbox) 증거 수집·검증·문서화(HTML/PDF/Excel) 파이프라인이다. 주요 실행점은 `main.py`, `run_server.py`, `app.py`.
- 아키텍처 핵심: UnifiedArchitecture(Service registry) 기반의 모듈식 시스템. 설정은 `config.json` → SystemConfig로 로드되어 서비스들이 초기화된다 (`src/core/unified_architecture.py`).

## 빠른 작업 흐름(자주 쓰는 커맨드 예시)

- 로컬 의존성 설치: `pip install -r requirements.txt` (프로젝트 루트)
- 개발 웹서버: `python run_server.py` 또는 `python main.py --web --port 8080`
- CLI 처리(파일): `python main.py email_files/sample.mbox --party 앉` (예시)
- Docker: `docker-compose up -d` (서비스: `email-parser`, 선택적 `redis`)
- 단일 테스트/스모크: `python test_phase1.py` (파일별 테스트 스크립트가 많음)

## 코드·패턴 관찰 (구체적 규칙)

- Flask 팩토리: 웹 앱은 팩토리 패턴으로 생성됨. 구현 위치 `src/web/app_factory.py` 또는 `src/web/app.py`. 서비스 컨텍스트(UnifiedArchitecture)를 앱 팩토리에 전달해야 함.
- 서비스 검색/등록: 서비스는 `UnifiedArchitecture.get_service(name)`로 접근. 새 서비스 추가 시 `src/core/unified_architecture.py`에 등록 관례를 따르되, 설정 기반 등록(또는 플러그인 방식)을 우선 확인.
- 설정 사용: 전역 설정은 `config.json`에 있음. 작업 시 경로를 하드코딩하지 말고 SystemConfig 또는 UnifiedArchitecture.config를 사용.
- 출력/데이터 디렉터리: `processed_emails/`, `uploads/`, `logs/`, `temp/`, `data/`가 런타임에 생성/사용됨. 테스트나 CI에서 파일 권한·쓰기 가능 여부를 확인할 것.
- CLI 인자 규칙: 선택 인자(예: `--select-emails`, `--select-pdfs`)는 문자열 형태('all'|'none'|'1,3,5')를 사용한다. 이를 파싱하는 유틸(예: `parse_selection_argument`)을 재사용.

## 통합 포인트 / 외부 의존성

- Redis + RQ: `docker-compose.yml`에 정의되어 있으나 로컬 개발에서는 선택적이다. Redis가 없을 때는 `src/web/upload_stream.py`의 로컬 폴백을 사용함(문서화 주석 참조).
- 데이터 저장소: 기본은 파일/로컬(예: SQLite나 파일시스템)로 보이며, 프로덕션 이동 시 Postgres 같은 DB로 교체 권장(이미 Docker 주석에 명시).
- 보안/해시: 증거 무결성 검증(예: SHA-256) 패턴 존재 — 새로운 암호화·해시 라이브러리 추가 시 `requirements.txt` 업데이트 필요.

## 변경/PR 작성 시 에이전트 규칙 (구체적)

1. 작은 변경을 선호: 한 PR은 하나의 논리적 변경(버그/기능)만 포함.
2. 의존성 변경: `requirements.txt`를 변경하면 즉시 보안 스캔을 트리거해야 함 — 레포에 포함된 `.github/instructions/codacy.instructions.md`를 따를 것(가능하면 `codacy_cli_analyze --tool trivy` 또는 조직 규칙에 따름).
3. 파일 수정 시: 관련 유닛/통합 테스트(있는 경우)를 실행해 빌드/런타임 에러를 방지. 빠른 스모크: `python run_server.py` 또는 `python main.py --test`.
4. 로그/디렉터리: 변경으로 인해 새 디렉터리가 필요하면 `run_server.py`/`app.py`에서 생성하는 관행(예: `uploads`, `processed_emails`, `logs`, `temp`)과 동일하게 처리.

## 피해야 할 실수 (코드베이스에서 자주 발생할 수 있는 것)

- Redis 미존재 환경에서 RQ 워커를 기대하는 변경 — 로컬 폴백을 확인하고 `docker-compose.yml` 주석을 읽을 것.
- 설정을 직접 하드코딩: 항상 `config.json` 사용 또는 SystemConfig를 통해 주입.
- 글로벌 상태 변경시 서비스 레지스트리에 등록 누락 — 새 서비스는 UnifiedArchitecture의 생명주기(초기화/cleanup)에 포함돼야 함.

## 참고할 주요 파일/디렉터리

- 진입점: `main.py`, `run_server.py`, `app.py`
- 아키텍처/설정: `src/core/unified_architecture.py`, `src/core/SystemConfig` (파일 경로로 존재함)
- 웹/플라스크: `src/web/app_factory.py`, `src/web/app.py`, `templates/`, `static/`
- 메일 파서/프로세서: `src/mail_parser/` (processor, reporter 등)
- Docker / 배포: `Dockerfile`, `docker-compose.yml`
- 설정 예: `config.json`, `requirements.txt`

---

필요하시면 이 문서를 더 세분화(예: 서비스 등록 샘플 코드, 테스트 러너 예제, CI 체크리스트)해 드리겠습니다. 이 초안에서 빠졌거나 더 설명이 필요한 세부 항목이 있나요?
