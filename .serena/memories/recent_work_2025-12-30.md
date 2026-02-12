# Phase 1-2 작업 완료 (2025-12-30)

## 완료 사항

### Phase 0: DB 통합 ✅
- email_parser.db에 evidence, chain_entry, jobs, timelines, timeline_events 5개 테이블 추가
- evidence_store.py, job_store.py, log_store.py, db_manager.py → email_parser.db 사용으로 전환
- job_store.db, logs.db 삭제

### Phase 1: 모델 리팩토링 ✅
- `src/core/models/timeline_model.py` 전면 재작성:
  - TimelineEventType: EMAIL, EMAIL_SENT/RECEIVED/REPLIED, ATTACHMENT_ADDED, EVIDENCE_CREATED, ADDITIONAL_EVIDENCE, DOCUMENT, PROCESSING_STARTED/COMPLETED
  - TimelineEvent: DB timeline_events 호환 dataclass (to_db_dict, from_db_row, to_dict, compute_hash)
  - TimelineModel: DB timelines 호환 dataclass (to_db_dict, from_db_row, to_dict, from_dict, update_date_range, compute_hash)
  - 레거시 호환: event_id, timeline_id, created_date 필드 유지

- `src/mail_parser/models/timeline_model.py` 신규: re-export from src.core.models
- `src/mail_parser/timeline.py` - TimelineBuilder 전면 구현:
  - build_from_emails(): EmailModel/dict 리스트 → TimelineModel
  - save_timeline/update_timeline: DB 저장
  - load_timeline/list_timelines/delete_timeline: DB 조회/삭제
  - add_event/update_event/delete_event/reorder_events/get_event: 이벤트 CRUD
  - DB 경로: data/db/email_parser.db

### Phase 2: TimelineService CRUD ✅ (완료)
- `src/services/timeline_service.py` 확장:
  - DB CRUD: create_timeline, get_timeline, list_timelines, update_timeline_meta, delete_timeline
  - 이벤트 CRUD: create_event, update_event, delete_event, reorder_events
  - self._builder = TimelineBuilder() 내부 사용
  - 기존 레거시 메서드(generate_timeline_from_evidence 등) 유지

## Phase 3-7 완료 (2026-02-12)

### Phase 3: REST API ✅
- timeline_routes.py에 10개 CRUD + 1 export + 1 from-emails 엔드포인트 추가
- /api/timelines (GET/POST), /api/timelines/<id> (GET/PUT/DELETE)
- /api/timelines/<id>/events (POST), events/<eid> (PUT/DELETE), events/reorder (PUT)
- /api/timelines/<id>/export/<fmt> (GET), /api/timelines/from-emails (POST)

### Phase 4: 내보내기 ✅
- src/timeline/exporters/ 모듈: base.py, pptx_exporter.py, docx_exporter.py, html_exporter.py
- Strategy 패턴 (TimelineExporter ABC)
- PPT ~32KB, Word ~37KB, HTML ~4KB

### Phase 5: UI 편집기 ✅
- templates/timeline_editor.html: SortableJS 드래그앤드롭, 인라인 편집, 모달 추가/수정
- /timeline_editor 라우트, _nav.html에 네비게이션 링크
- 타임라인 목록 좌측, 편집 패널 우측 레이아웃

### Phase 6: 스트리밍 연결 ✅
- /api/timelines/from-emails: 이메일 dict 리스트 → 타임라인 자동 생성

### Phase 7: Hash Chain 무결성 ✅
- save_timeline: 이벤트 hash + 타임라인 hash 자동 계산
- add_event/update_event/delete_event: hash 재계산 + _refresh_timeline_hash
- 이벤트 추가→hash 변경, 삭제→원래 hash 복원 검증 완료

### E2E 테스트: 23/23 PASS ✅