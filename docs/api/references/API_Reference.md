# 이메일 증거 처리 시스템 레퍼런스 📧

**버전**: 2.0
**생성일**: 2025-09-03 15:23:01
**설명**: 한국 법원 제출용 이메일 증거 처리 및 분류 시스템

## 📊 시스템 현황

- **총 엔드포인트**: 62개
- **웹 라우트**: 38개
- **API 라우트**: 18개
- **팩토리 라우트**: 6개
- **데이터 모델**: 1개

## 📋 목차

- [웹 라우트](#웹-라우트)
- [팩토리 라우트](#팩토리-라우트)
- [API 엔드포인트](#api-엔드포인트)
- [데이터 모델](#데이터-모델)
- [템플릿 정보](#템플릿-정보)
- [설정 정보](#설정-정보)

---

## 🌐 웹 라우트

### `GET` `/`

**함수**: `index`
**파일**: `src\web\routes.py`
**설명**: 메인 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `POST` `/add_evidence`

**함수**: `add_evidence`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 파일 등록

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/additional_evidence`

**함수**: `additional_evidence`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 관리 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/admin`

**함수**: `admin_page`
**파일**: `src\web\routes.py`
**설명**: 관리자 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `POST` `/api/admin/cleanup`

**함수**: `cleanup_tasks`
**파일**: `src\web\routes.py`
**설명**: 비정상 종료된 작업들 정리

**응답**: JSON - JSON 응답

---

### `GET` `/api/admin/tasks`

**함수**: `get_all_tasks`
**파일**: `src\web\routes.py`
**설명**: 모든 진행 중인 작업 확인 (관리용)

**응답**: JSON - JSON 응답

---

### `GET` `/api/check_processed_emails`

**함수**: `api_check_processed_emails`
**파일**: `src\web\routes.py`
**설명**: 처리된 이메일 존재 여부 확인 API

**응답**: JSON - JSON 응답

---

### `GET` `/api/docs`

**함수**: `api_docs`
**파일**: `src\web\routes.py`
**설명**: API 문서 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/api/emails/<file_id>`

**함수**: `api_email_list`
**파일**: `src\web\routes.py`
**설명**: API: 이메일 목록 조회

**파라미터**:
- `file_id` (Any): file_id 파라미터

**응답**: JSON - JSON 응답

---

### `GET` `/api/evidence_categories`

**함수**: `api_evidence_categories`
**파일**: `src\web\routes.py`
**설명**: 증거 카테고리 정보 API

**응답**: JSON - JSON 응답

---

### `GET` `/api/evidence_progress/<task_id>`

**함수**: `get_evidence_progress`
**파일**: `src\web\routes.py`
**설명**: 증거 생성 진행 상황 API

**파라미터**:
- `task_id` (Any): task_id 파라미터

**응답**: JSON - JSON 응답

---

### `GET` `/api/files`

**함수**: `api_file_list`
**파일**: `src\web\routes.py`
**설명**: API: 업로드된 파일 목록

**응답**: JSON - JSON 응답

---

### `GET` `/api/progress/<task_id>`

**함수**: `get_progress`
**파일**: `src\web\routes.py`
**설명**: 진행 상황 API

**파라미터**:
- `task_id` (Any): task_id 파라미터

**응답**: JSON - JSON 응답

---

### `POST` `/api/upload`

**함수**: `api_upload`
**파일**: `src\web\routes.py`
**설명**: API: 파일 업로드

**응답**: JSON - JSON 응답

---

### `GET` `/api/verify_integrity`

**함수**: `api_verify_integrity`
**파일**: `src\web\routes.py`
**설명**: 법원 제출용 무결성 검증 API

**응답**: JSON - JSON 응답

---

### `POST` `/delete_evidence/<file_id>`

**함수**: `delete_evidence`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 삭제

**파라미터**:
- `file_id` (Any): file_id 파라미터

**응답**: Redirect - HTTP 리다이렉션

---

### `GET` `/download/<path:filename>`

**함수**: `download_file`
**파일**: `src\web\routes.py`
**설명**: 파일 다운로드

**파라미터**:
- `filename` (Any): filename 파라미터

**응답**: Unknown - 응답

---

### `GET` `/download_court_certificate`

**함수**: `download_court_certificate`
**파일**: `src\web\routes.py`
**설명**: 법원 제출용 무결성 증명서 다운로드

**응답**: Unknown - 응답

---

### `GET` `/download_evidence_index`

**함수**: `download_evidence_index`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 목록서 다운로드

**응답**: Unknown - 응답

---

### `GET` `/download_timeline_excel`

**함수**: `download_timeline_excel`
**파일**: `src\web\routes.py`
**설명**: 통합 타임라인 Excel 다운로드

**응답**: Unknown - 응답

---

### `GET` `/download_verification_report`

**함수**: `download_verification_report`
**파일**: `src\web\routes.py`
**설명**: 무결성 검증 보고서 다운로드

**응답**: Unknown - 응답

---

### `GET` `POST` `/edit_evidence/<file_id>`

**함수**: `edit_evidence`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 편집

**파라미터**:
- `file_id` (Any): file_id 파라미터

**응답**: Redirect - HTTP 리다이렉션

---

### `GET` `/email/<file_id>/<int:email_index>`

**함수**: `email_detail`
**파일**: `src\web\routes.py`
**설명**: 이메일 상세 페이지

**파라미터**:
- `file_id` (Any): file_id 파라미터
- `email_index` (Any): email_index 파라미터

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/emails/<file_id>`

**함수**: `email_list`
**파일**: `src\web\routes.py`
**설명**: 이메일 목록 페이지 - 선택적 증거 생성 기능 포함

**파라미터**:
- `file_id` (Any): file_id 파라미터

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/evidence`

**함수**: `evidence_list`
**파일**: `src\web\routes.py`
**설명**: 증거 목록 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/evidence/<folder_name>`

**함수**: `evidence_detail`
**파일**: `src\web\routes.py`
**설명**: 증거 상세 페이지

**파라미터**:
- `folder_name` (Any): folder_name 파라미터

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/export_additional_evidence`

**함수**: `export_additional_evidence`
**파일**: `src\web\routes.py`
**설명**: 추가 증거 법원 제출용 패키징

**응답**: Unknown - 응답

---

### `POST` `/generate_evidence/<file_id>`

**함수**: `generate_evidence`
**파일**: `src\web\routes.py`
**설명**: 선택된 이메일들에 대해 증거 생성

**파라미터**:
- `file_id` (Any): file_id 파라미터

**응답**: Unknown - 응답

---

### `GET` `/generate_timeline_package`

**함수**: `generate_timeline_package`
**파일**: `src\web\routes.py`
**설명**: 법원 제출용 타임라인 패키지 생성

**응답**: Unknown - 응답

---

### `GET` `/integrated_timeline`

**함수**: `integrated_timeline`
**파일**: `src\web\routes.py`
**설명**: 통합 타임라인 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/integrity`

**함수**: `integrity`
**파일**: `src\web\routes.py`
**설명**: 무결성 검증 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `POST` `/process_selected`

**함수**: `process_selected_emails`
**파일**: `src\web\routes.py`
**설명**: 선택된 이메일들을 HTML/PDF로 처리

**응답**: JSON - JSON 응답

---

### `GET` `/processing/<task_id>`

**함수**: `processing_status`
**파일**: `src\web\routes.py`
**설명**: 처리 진행 상황 페이지

**파라미터**:
- `task_id` (Any): task_id 파라미터

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/search`

**함수**: `search_page`
**파일**: `src\web\routes.py`
**설명**: 검색 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/settings`

**함수**: `settings_page`
**파일**: `src\web\routes.py`
**설명**: 설정 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/timeline`

**함수**: `timeline_page`
**파일**: `src\web\routes.py`
**설명**: 타임라인 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `POST` `/upload`

**함수**: `upload_file`
**파일**: `src\web\routes.py`
**설명**: 파일 업로드 및 처리

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/verify_integrity`

**함수**: `verify_integrity`
**파일**: `src\web\routes.py`
**설명**: 법원 제출용 무결성 검증 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

---

## 🏭 팩토리 라우트

### `GET` `/`

**함수**: `index`
**파일**: `src\web\app_factory.py`
**설명**: 메인 대시보드

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/api`

**함수**: `api_info`
**파일**: `src\web\app_factory.py`
**설명**: API 정보 엔드포인트

**응답**: JSON - JSON 응답

---

### `GET` `/docs`

**함수**: `api_docs`
**파일**: `src\web\app_factory.py`
**설명**: API 문서 페이지

**응답**: HTML - HTML 템플릿 렌더링

---

### `GET` `/health`

**함수**: `health_check`
**파일**: `src\web\app_factory.py`
**설명**: 헬스체크 (Docker/로드밸런서용)

**응답**: JSON - JSON 응답

---

### `GET` `/system/status`

**함수**: `system_status`
**파일**: `src\web\app_factory.py`
**설명**: 시스템 상태 페이지

**응답**: JSON - JSON 응답

---

### `GET` `POST` `/upload`

**함수**: `upload`
**파일**: `src\web\app_factory.py`
**설명**: 파일 업로드 페이지 (기본 구현)

**응답**: JSON - JSON 응답

---

---

## 🔌 API 엔드포인트

### `POST` `/api/emails/load`

**함수**: `api_load_emails`
**파일**: `src\web\api.py`
**설명**: 이메일 로드 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X POST "http://localhost:5000/api/emails/load"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `POST` `/api/emails/process`

**함수**: `api_process_emails`
**파일**: `src\web\api.py`
**설명**: 이메일 처리 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X POST "http://localhost:5000/api/emails/process"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/emails/search`

**함수**: `api_search_emails`
**파일**: `src\web\api.py`
**설명**: 이메일 검색 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/emails/search"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/emails/statistics`

**함수**: `api_email_statistics`
**파일**: `src\web\api.py`
**설명**: 이메일 통계 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/emails/statistics"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/evidence`

**함수**: `api_evidence_list`
**파일**: `src\web\api.py`
**설명**: 증거 목록 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/evidence"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/evidence/<folder_name>`

**함수**: `api_evidence_detail`
**파일**: `src\web\api.py`
**설명**: 증거 상세 API

**파라미터**:
- `folder_name` (Any): folder_name 파라미터

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/evidence/<folder_name>"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `DELETE` `/api/evidence/<folder_name>`

**함수**: `api_delete_evidence`
**파일**: `src\web\api.py`
**설명**: 증거 삭제 API

**파라미터**:
- `folder_name` (Any): folder_name 파라미터

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X DELETE "http://localhost:5000/api/evidence/<folder_name>"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/evidence/export`

**함수**: `api_export_evidence`
**파일**: `src\web\api.py`
**설명**: 증거 목록 내보내기 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/evidence/export"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/evidence/integrity`

**함수**: `api_evidence_integrity`
**파일**: `src\web\api.py`
**설명**: 증거 무결성 검증 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/evidence/integrity"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/files/info`

**함수**: `api_file_info`
**파일**: `src\web\api.py`
**설명**: 파일 정보 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/files/info"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/files/list`

**함수**: `api_list_files`
**파일**: `src\web\api.py`
**설명**: 파일 목록 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/files/list"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `POST` `/api/system/cleanup`

**함수**: `api_cleanup`
**파일**: `src\web\api.py`
**설명**: 시스템 정리 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X POST "http://localhost:5000/api/system/cleanup"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/system/disk-usage`

**함수**: `api_disk_usage`
**파일**: `src\web\api.py`
**설명**: 디스크 사용량 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/system/disk-usage"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/timeline`

**함수**: `api_timeline`
**파일**: `src\web\api.py`
**설명**: 타임라인 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/timeline"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/api/timeline/export`

**함수**: `api_timeline_export`
**파일**: `src\web\api.py`
**설명**: 타임라인 내보내기 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/api/timeline/export"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `POST` `/api/timeline/filter`

**함수**: `api_timeline_filter`
**파일**: `src\web\api.py`
**설명**: 타임라인 필터링 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X POST "http://localhost:5000/api/timeline/filter"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `GET` `/docs-status`

**함수**: `docs_status`
**파일**: `src\docs\api_endpoints.py`
**설명**: 문서 상태 확인 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X GET "http://localhost:5000/docs-status"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

### `POST` `/regenerate-docs`

**함수**: `regenerate_docs`
**파일**: `src\docs\api_endpoints.py`
**설명**: 문서 재생성 API

**응답**: JSON - JSON 응답


**사용 예시**:
```bash
curl -X POST "http://localhost:5000/regenerate-docs"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {},
  "message": "성공"
}
```

---

---

## 📊 데이터 모델

### 📋 SystemConfig

**파일**: `src\core\unified_architecture.py`
**설명**: 시스템 통합 설정

**필드**:
- `app_name: str` - app_name 필드 (기본값: `이메일 증거 처리 시스템`)
- `version: str` - version 필드 (기본값: `2.0.0`)
- `debug_mode: bool` - debug_mode 필드 (기본값: `False`)
- `project_root: Path` - project_root 필드
- `config_data: Dict[Any]` - config_data 필드
- `uploads_dir: Path` - uploads_dir 필드
- `processed_dir: Path` - processed_dir 필드
- `temp_dir: Path` - temp_dir 필드
- `logs_dir: Path` - logs_dir 필드
- `docs_dir: Path` - docs_dir 필드

---


---

## 🎨 템플릿 정보

**총 템플릿**: 10개

### 📄 admin.html

- **경로**: `templates\admin.html`
- **크기**: 7296 bytes
- **블록**: `scripts`, `content`

### 📄 api.html

- **경로**: `templates\api.html`
- **크기**: 7671 bytes
- **블록**: `scripts`, `content`

### 📄 base.html

- **경로**: `templates\base.html`
- **크기**: 4240 bytes
- **변수**: `page_title`, `url_for`, `message`
- **블록**: `scripts`, `title`, `content`

### 📄 email_detail.html

- **경로**: `templates\email_detail.html`
- **크기**: 11355 bytes
- **변수**: `email.subject`, `email.date`, `email.sender`, `email.attachments`, `email_index`, `attachment.download_url`, `email.full_content.text`, `attachment.filename`, `email.recipients`, `email.id`, `email.full_content.html`, `url_for`, `file_id`
- **블록**: `title`, `content`

### 📄 email_list.html

- **경로**: `templates\email_list.html`
- **크기**: 30147 bytes
- **변수**: `email.preview`, `emails`, `email.date.strftime`, `email.subject`, `email.sender`, `filename`, `loop.index0`, `email.attachments_count`, `email.sender.split`, `url_for`, `file_id`
- **블록**: `scripts`, `content`

### 📄 email_list_new.html

- **경로**: `templates\email_list_new.html`
- **크기**: 14208 bytes
- **변수**: `emails`, `email.subject`, `email.sender`, `email.attachments`, `filename`, `loop.index0`, `email.date`, `loop.index`, `url_for`, `file_id`
- **블록**: `title`, `content`

### 📄 index.html

- **경로**: `templates\index.html`
- **크기**: 11377 bytes
- **변수**: `service`, `system_status.project_root`, `system_status.registered_services`, `system_status.timestamp`, `title`, `evidence_stats.get`

### 📄 index_new.html

- **경로**: `templates\index_new.html`
- **크기**: 18803 bytes
- **변수**: `stats.total_files`, `stats.total_emails`, `stats.success_rate`, `stats.processed_files`, `url_for`
- **블록**: `title`, `content`

### 📄 processing.html

- **경로**: `templates\processing.html`
- **크기**: 8316 bytes
- **변수**: `progress.task_name`, `progress.current_message`, `task_id`, `progress.progress`, `progress.error`, `progress.updated_at`, `progress.started_at`
- **블록**: `scripts`, `content`

### 📄 upload.html

- **경로**: `templates\upload.html`
- **크기**: 10755 bytes
- **변수**: `url_for`
- **블록**: `scripts`, `content`


---

## ⚙️ 설정 정보

**설정 파일**: `config.json`

**설정 카테고리**: `_comment`, `_usage`, `exclude_keywords`, `exclude_senders`, `exclude_domains`, `date_range`, `required_keywords`, `processing_options`, `forensic_settings`, `output_settings`, `compliance_standards`, `performance_monitoring`

**주요 설정**:
- `_comment`: `메일 파싱 필터링 설정 파일`
- `_usage`: `python main.py email_files/example.mbox --party 갑 --config config.json`
- `exclude_keywords`: (복합 설정)
- `exclude_senders`: (복합 설정)
- `exclude_domains`: (복합 설정)


---

## ❌ 에러 코드

### HTTP 상태 코드

| 코드 | 설명 | 대응 방법 |
|------|------|-----------|
| 200  | 성공 | - |
| 400  | 잘못된 요청 | 요청 파라미터 확인 |
| 404  | 리소스 없음 | URL 경로 확인 |
| 413  | 파일 크기 초과 | 2GB 이하 파일 사용 |
| 500  | 서버 오류 | 서버 로그 확인 |

### 커스텀 에러 코드

| 코드 | 메시지 | 설명 |
|------|--------|------|
| E001 | 파일 형식 오류 | 지원되지 않는 파일 형식 |
| E002 | 파싱 실패 | 손상된 메일 파일 |
| E003 | 메모리 부족 | 시스템 리소스 부족 |
| E004 | 권한 오류 | 파일 접근 권한 없음 |

