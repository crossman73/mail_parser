# 라우팅 맵 (Routing Map)

> 생성일: 2025-12-30
> Phase 1 완료 후 상태
> 총 라우트: 약 70개

## 📊 Blueprint 구조

| Blueprint | url_prefix | 파일 | 라우트 수 | 설명 |
|-----------|-----------|------|----------|------|
| **main** | - | routes.py | ~55 | 메인 애플리케이션 라우트 |
| **admin** | '' | admin_routes.py | 5 | 관리자 기능 |
| **ui** | '' | ui_routes.py | 1 | 실험적 UI |
| **upload_bp** | /api | upload_stream.py | 2 | 업로드 API |
| **api** | - | api.py | 18 | REST API (register 방식) |
| **system** | - | app.py | 5 | 시스템 라우트 |

## 🗺️ 주요 라우트

### 메인 페이지 (routes.py)
- `GET /` - 메인 페이지
- `GET /upload` - 파일 업로드 페이지
- `POST /upload` - 파일 업로드 처리

### 이메일 관련
- `GET /emails/<file_id>` - 이메일 목록
- `GET /email/<file_id>/<int:email_index>` - 이메일 상세
- `POST /process_selected` - 선택 이메일 처리

### 증거 관리
- `GET /evidence` - 증거 목록
- `GET /evidence/<folder_name>` - 증거 상세
- `POST /generate_evidence/<file_id>` - 증거 생성
- `GET /evidence_file/<file_id>` - 증거 파일 뷰어
- `GET /evidence_management` - 증거 관리 페이지
- `GET /additional_evidence` - 추가 증거 목록
- `GET /add_evidence` - 추가 증거 등록
- `POST /add_evidence` - 추가 증거 저장
- `GET /edit_evidence/<file_id>` - 증거 편집
- `POST /edit_evidence/<file_id>` - 증거 수정
- `POST /delete_evidence/<file_id>` - 증거 삭제

### 타임라인
- `GET /timeline` - 타임라인 페이지
- `GET /integrated_timeline` - 통합 타임라인
- `GET /generate_timeline_package` - 법원 제출용 패키지
- `GET /download_timeline_excel` - Excel 다운로드

### 무결성 검증
- `GET /integrity` - 무결성 검증 페이지
- `GET /verify_integrity` - 검증 수행
- `GET /api/verify_integrity` - 검증 API
- `GET /api/check_processed_emails` - 이메일 확인
- `GET /download_verification_report` - 검증 보고서
- `GET /download_court_certificate` - 법원 제출용 증명서

### 로그 뷰어
- `GET /logs` - 로그 뷰어 페이지
- `GET /api/logs` - 로그 조회 API
- `GET /api/logs/download` - 로그 다운로드
- `POST /api/logs/clear` - 로그 삭제
- `GET /api/logs/files` - 로그 파일 목록
- `GET /api/logs/file/<filename>` - 로그 파일 내용
- `GET /api/logs/file/<filename>/download` - 로그 파일 다운로드

### 관리자 (admin Blueprint)
- `GET /admin` - 관리자 대시보드
- `GET /admin/evidence/<int:evidence_id>` - 증거 상세
- `GET /admin/jobs` - 작업 목록
- `DELETE /api/admin/job/<job_id>` - 작업 삭제
- `GET /admin/settings` - 시스템 설정
- `GET /admin/logs` - 관리자 로그
- `GET /api/admin/logs` - 로그 API
- `POST /api/admin/settings/init` - 설정 초기화
- `GET /api/admin/settings` - 설정 조회
- `POST /api/admin/settings` - 설정 추가
- `PUT /api/admin/settings/<int:setting_id>` - 설정 수정
- `DELETE /api/admin/settings/<int:setting_id>` - 설정 삭제
- `GET /api/admin/settings/history` - 설정 변경 이력
- `POST /api/admin/settings/export` - 설정 내보내기
- `POST /api/admin/settings/import` - 설정 가져오기

### 시스템 (app.py)
- `GET /health` - 헬스체크
- `GET /api/system/status` - 시스템 상태 API
- `GET /system/status` - 시스템 상태 페이지
- `GET /system` - 시스템 정보
- `GET /docs` - API 문서

### API (api.py - register_api_routes)
- `POST /api/emails/load` - 이메일 로드
- `POST /api/emails/process` - 이메일 처리
- `GET /api/emails/search` - 이메일 검색
- `GET /api/emails/statistics` - 통계
- `GET /api/evidence` - 증거 목록 API
- `GET /api/evidence/<folder_name>` - 증거 상세 API
- `DELETE /api/evidence/<folder_name>` - 증거 삭제
- `GET /api/evidence/export` - 증거 내보내기
- `GET /api/evidence/integrity` - 무결성 확인
- `GET /api/timeline` - 타임라인 API
- `POST /api/timeline/filter` - 타임라인 필터
- `GET /api/timeline/export` - 타임라인 내보내기
- `GET /api/files/info` - 파일 정보
- `GET /api/files/list` - 파일 목록
- `GET /api/upload` - 업로드 상태
- `POST /api/upload` - 파일 업로드
- `GET /api/system/disk-usage` - 디스크 사용량
- `POST /api/system/cleanup` - 시스템 정리

### 업로드 (upload_bp Blueprint)
- `POST /api/upload/stream` - 스트림 업로드
- `GET /api/upload/job/<job_id>` - 작업 상태 조회

### UI 실험 (ui Blueprint)
- `GET /ui/wireframe` - 와이어프레임

## ⚠️ 중복 가능성

### url_prefix 충돌
- **admin** (url_prefix='') + **ui** (url_prefix='')
  - 현재는 라우트 경로가 겹치지 않아 문제 없음
  - `/admin/*` vs `/ui/*`

### 라우트 경로 중복 (Phase 1에서 제거됨)
- ~~`/evidence` (2곳)~~ ✓ 제거
- ~~`/timeline` (2곳)~~ ✓ 제거
- ~~`/emails` (2곳)~~ ✓ 제거
- ~~`/integrated_timeline` (2곳)~~ ✓ 제거
- ~~`/generate_timeline_package` (2곳)~~ ✓ 제거
- ~~`/download_timeline_excel` (2곳)~~ ✓ 제거

## 📋 Phase 3 계획

routes.py(1641줄)를 다음과 같이 분할 예정:

1. **main_routes.py** (~300줄)
   - /, /upload, /processing, /search, /settings

2. **evidence_routes.py** (~400줄)
   - /evidence/*, /evidence_management, /additional_evidence, /add_evidence, /edit_evidence, /delete_evidence

3. **timeline_routes.py** (~300줄)
   - /timeline, /integrated_timeline, /generate_timeline_package, /download_timeline_excel

4. **integrity_routes.py** (~200줄)
   - /integrity, /verify_integrity, /download_verification_report, /download_court_certificate

5. **logs_routes.py** (~300줄)
   - /logs, /api/logs/*

6. **email_routes.py** (~200줄)
   - /emails/*, /email/*, /process_selected

## 🔍 Phase 2 검증 완료

- ✅ 웹서버 정상 작동 (재시작 후 테스트 통과)
- ✅ 주요 엔드포인트 접근 가능
  - / - HTTP 200
  - /health - HTTP 200
  - /admin - HTTP 200
  - /admin/settings - HTTP 200
  - /system/status - HTTP 200
  - /docs - HTTP 200
