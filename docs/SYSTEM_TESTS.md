# 시스템 테스트 관리 기능

## 개요
관리자가 시스템의 핵심 기능들을 웹 UI에서 직접 테스트하고 결과를 확인할 수 있는 시스템 테스트 관리 기능입니다.

## 주요 기능

### 1. DB 스키마
- **system_tests**: 테스트 정의 저장
  - test_key: 고유 식별자
  - test_name: 테스트명
  - test_category: 카테고리 (web, database, email, forensic, api, system)
  - test_module: Python 모듈 경로
  - test_function: 실행할 함수명
  - is_enabled: 활성화 여부
  - timeout_seconds: 타임아웃 설정
  - display_order: 표시 순서

- **test_executions**: 테스트 실행 이력
  - test_id: 테스트 ID (FK)
  - execution_time: 실행 시간
  - status: 상태 (success/failed/error)
  - result_message: 결과 메시지
  - error_detail: 오류 상세
  - duration_ms: 소요 시간 (밀리초)

### 2. 테스트 관리 클래스

#### SystemTestManager (`src/database/email_db.py`)
```python
test_manager = SystemTestManager()

# 테스트 CRUD
test_manager.add_test(...)
test_manager.get_all_tests(category=None, enabled_only=False)
test_manager.get_test_by_key(test_key)
test_manager.update_test(test_key, **kwargs)
test_manager.delete_test(test_key)

# 실행 이력
test_manager.save_execution(...)
test_manager.get_execution_history(test_key=None, limit=50)
test_manager.get_test_categories()
```

#### TestExecutor (`src/system_tests/executor.py`)
```python
test_executor = TestExecutor()

# 단일 테스트 실행
result = test_executor.execute_test(module, function, timeout)

# 여러 테스트 실행
results = test_executor.execute_multiple_tests(tests)
```

### 3. 기본 테스트 (10개)

| 테스트 | 카테고리 | 설명 |
|--------|----------|------|
| test_web_app | web | Flask 앱 초기화 및 메인 페이지 |
| test_health_check | web | 헬스체크 엔드포인트 |
| test_database | database | DB 연결 및 쿼리 |
| test_config | system | 설정 파일 검증 |
| test_directories | system | 디렉토리 구조 검증 |
| test_email_processor | email | 이메일 프로세서 초기화 |
| test_forensic | forensic | 포렌식 서비스 초기화 |
| test_api_endpoints | api | API 엔드포인트 응답 |
| test_system_settings | system | 설정 CRUD 기능 |
| test_disk_space | system | 디스크 공간 확인 |

### 4. API 엔드포인트

#### 테스트 관리
- `GET /api/admin/tests` - 전체 테스트 목록
- `GET /api/admin/tests/<test_key>` - 특정 테스트 조회
- `POST /api/admin/tests` - 테스트 추가
- `PUT /api/admin/tests/<test_key>` - 테스트 수정
- `DELETE /api/admin/tests/<test_key>` - 테스트 삭제

#### 테스트 실행
- `POST /api/admin/tests/<test_key>/execute` - 단일 테스트 실행
- `POST /api/admin/tests/execute-all` - 전체 테스트 실행

#### 실행 이력
- `GET /api/admin/tests/<test_key>/history` - 테스트별 이력
- `GET /api/admin/tests/history` - 전체 이력

### 5. UI 기능

#### `/admin/system-tests` 페이지
- 테스트 목록 표시 (카테고리별 탭)
- 통계 카드 (전체/성공/실패/오류)
- 개별 테스트 실행 버튼
- 전체 테스트 일괄 실행
- 테스트 추가/수정/삭제
- 실행 이력 조회
- 마지막 실행 결과 표시

## 사용 방법

### 1. 초기 설정
```bash
# 기본 테스트 데이터 추가
python scripts/init_system_tests.py
```

### 2. 웹 UI 접근
```
http://localhost:5000/admin/system-tests
```

### 3. 새 테스트 추가
1. "테스트 추가" 버튼 클릭
2. 테스트 정보 입력
   - 테스트 키: `test_my_feature`
   - 모듈: `src.system_tests.core_tests`
   - 함수: `test_my_feature`
3. 저장

### 4. 테스트 함수 작성 (`src/system_tests/core_tests.py`)
```python
def test_my_feature() -> Dict[str, Any]:
    """새로운 기능 테스트"""
    try:
        # 테스트 로직
        result = my_function()

        if result == expected:
            return {
                'status': 'success',
                'message': '테스트 통과'
            }
        else:
            return {
                'status': 'failed',
                'message': f'예상: {expected}, 실제: {result}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'테스트 중 오류: {str(e)}'
        }
```

### 5. 테스트 실행
- UI에서 개별 실행 버튼 클릭
- 또는 "전체 실행" 버튼으로 일괄 실행
- API로 직접 호출:
  ```bash
  curl -X POST http://localhost:5000/api/admin/tests/test_my_feature/execute
  ```

## 테스트 결과 형식

### 반환 형식
```python
{
    'status': 'success' | 'failed' | 'error',
    'message': '결과 메시지',
    'error_detail': '오류 상세 (선택적)'
}
```

- **success**: 테스트 통과
- **failed**: 테스트 실패 (예상과 다른 결과)
- **error**: 테스트 중 예외 발생

## 커밋 정보
- Commit: `7f37fcb`
- 날짜: 2025-12-30 19:08:10
- 브랜치: feature/admin-settings-clean

## 파일 구조
```
src/
  database/
    email_db.py              # SystemTestManager 추가
  system_tests/
    __init__.py
    executor.py              # TestExecutor
    core_tests.py            # 기본 테스트 함수들
  web/
    admin_routes.py          # API 엔드포인트 추가

templates/
  admin_system_tests.html    # UI 페이지

scripts/
  init_system_tests.py       # 초기 데이터 설정
```

## 확장 방법

### 1. 새로운 카테고리 추가
테스트 추가 시 카테고리 선택 항목에서 사용할 수 있습니다.

### 2. 새로운 테스트 모듈 추가
```python
# src/system_tests/my_tests.py
def test_new_feature():
    # ...
```

UI에서 모듈 경로를 `src.system_tests.my_tests`로 지정

### 3. 타임아웃 조정
각 테스트마다 개별적으로 타임아웃 설정 가능 (기본 30초)

### 4. 실행 이력 분석
`test_executions` 테이블에서 실행 통계 및 추이 분석 가능

## 주의사항
- 테스트 함수는 항상 딕셔너리를 반환해야 합니다
- 장시간 실행되는 테스트는 타임아웃을 적절히 설정하세요
- 데이터 변경을 수반하는 테스트는 주의해서 작성하세요
- 프로덕션 환경에서는 필요한 테스트만 활성화하세요
