# API 레퍼런스

> 최종 업데이트: 2026-02-06

## 기본 정보

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **인코딩**: UTF-8

## 이메일 API

### GET /api/emails
이메일 목록 조회

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "subject": "string",
      "sender": "string",
      "date": "2026-02-06T12:00:00Z",
      "has_attachments": true
    }
  ],
  "total": 100
}
```

### GET /api/emails/{id}
이메일 상세 조회

**Parameters**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | string | ✓ | 이메일 ID |

**Response**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "subject": "string",
    "sender": "string",
    "recipients": ["string"],
    "date": "2026-02-06T12:00:00Z",
    "body": "string",
    "attachments": [
      {
        "filename": "string",
        "size": 1024,
        "content_type": "string"
      }
    ]
  }
}
```

### POST /api/emails/parse
mbox 파일 파싱

**Request**
```json
{
  "file_path": "string"
}
```

**Response**
```json
{
  "success": true,
  "message": "파싱 완료",
  "email_count": 50
}
```

---

## 증거 API

### GET /api/evidence
증거 목록 조회

**Query Parameters**
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| per_page | int | 20 | 페이지당 항목 수 |
| category | string | - | 카테고리 필터 |

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "title": "string",
      "category": "string",
      "created_at": "2026-02-06T12:00:00Z",
      "hash": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

### POST /api/evidence
증거 생성

**Request**
```json
{
  "email_ids": ["string"],
  "category": "string",
  "description": "string"
}
```

**Response**
```json
{
  "success": true,
  "evidence_id": "string",
  "hash": "string"
}
```

### DELETE /api/evidence/{id}
증거 삭제 (소프트 삭제)

**Response**
```json
{
  "success": true,
  "message": "삭제 완료"
}
```

---

## 타임라인 API

### GET /api/timeline
타임라인 조회

**Query Parameters**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| start_date | string | 시작일 (YYYY-MM-DD) |
| end_date | string | 종료일 (YYYY-MM-DD) |

**Response**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-02-06",
      "events": [
        {
          "time": "12:00:00",
          "type": "email",
          "subject": "string",
          "participants": ["string"]
        }
      ]
    }
  ]
}
```

### POST /api/timeline/generate
타임라인 생성

**Request**
```json
{
  "evidence_ids": ["string"],
  "format": "json|excel|pdf"
}
```

**Response**
```json
{
  "success": true,
  "timeline_id": "string",
  "download_url": "/api/timeline/download/{id}"
}
```

---

## 무결성 API

### POST /api/integrity/verify
무결성 검증

**Request**
```json
{
  "evidence_id": "string"
}
```

**Response**
```json
{
  "success": true,
  "valid": true,
  "hash_chain": [
    {
      "index": 0,
      "hash": "string",
      "previous_hash": "string",
      "verified": true
    }
  ]
}
```

### GET /api/integrity/report/{id}
무결성 보고서 조회

**Response**
```json
{
  "success": true,
  "report": {
    "evidence_id": "string",
    "verified_at": "2026-02-06T12:00:00Z",
    "status": "valid",
    "chain_length": 10,
    "algorithm": "SHA-256"
  }
}
```

---

## 시스템 API

### GET /api/status
시스템 상태 조회

**Response**
```json
{
  "success": true,
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "database": "connected"
}
```

### GET /api/settings
설정 조회

**Response**
```json
{
  "success": true,
  "settings": {
    "theme": "dark",
    "language": "ko",
    "auto_backup": true
  }
}
```

### POST /api/settings
설정 저장

**Request**
```json
{
  "theme": "dark",
  "language": "ko"
}
```

---

## 에러 응답

모든 API는 에러 발생 시 다음 형식으로 응답합니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

### 에러 코드
| 코드 | HTTP 상태 | 설명 |
|------|----------|------|
| NOT_FOUND | 404 | 리소스를 찾을 수 없음 |
| VALIDATION_ERROR | 400 | 입력값 검증 실패 |
| INTEGRITY_ERROR | 400 | 무결성 검증 실패 |
| SERVER_ERROR | 500 | 서버 내부 오류 |
