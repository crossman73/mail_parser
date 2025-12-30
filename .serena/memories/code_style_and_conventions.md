# 코드 스타일 및 컨벤션

## Python 스타일 가이드

### PEP 8 준수
- 프로젝트는 PEP 8 스타일 가이드를 따름
- 들여쓰기: 4 스페이스
- 라인 길이: 80-100자 권장
- 인코딩: UTF-8

### Type Hints
권장하지만 필수는 아님
```python
def process_email(email_path: str, party: str = "갑") -> Dict[str, Any]:
    """이메일 처리 함수"""
    pass
```

### Docstring (Google 스타일)
모든 함수/클래스에 docstring 필수

```python
def create_app(config_path: str = None):
    """Flask 애플리케이션 생성
    
    Args:
        config_path: 설정 파일 경로 (선택)
    
    Returns:
        Flask 애플리케이션 인스턴스
        
    Raises:
        FileNotFoundError: 설정 파일을 찾을 수 없는 경우
    """
    pass
```

### 네이밍 컨벤션
- **변수/함수**: snake_case
  - `email_processor`, `create_app`, `get_user_data`
- **클래스**: PascalCase
  - `EmailProcessor`, `SettingsManager`, `DatabaseHandler`
- **상수**: UPPER_SNAKE_CASE
  - `MAX_FILE_SIZE`, `DEFAULT_CONFIG`, `DB_PATH`
- **Private 메서드**: 언더스코어 접두사
  - `_internal_method`, `_validate_input`

## 프로젝트 특화 스타일

### 한글 주석 및 메시지
- 사용자 대면 메시지: 한글 사용 권장
- 코드 주석: 한글/영어 혼용 가능
- Docstring: 한글 사용 가능

```python
def process_email(email_path: str):
    """이메일 처리 및 증거 생성"""
    print("✅ 이메일 처리 완료")
    # 내부 검증 수행
    return result
```

### 이모지 사용
로그 및 사용자 메시지에 이모지 적극 사용
```python
print("✅ 설정 DB 연결 성공")
print("📍 라우트 등록 시작...")
print("❌ 데이터베이스 연결 실패")
print("⚠️ 경고: 설정 파일 없음")
```

### 에러 처리
try-except 패턴 적극 활용
```python
try:
    from src.core.settings_manager import get_settings_manager
    settings = get_settings_manager()
    print("✅ 설정 관리자 초기화 완료")
except Exception as e:
    print(f"⚠️ 설정 관리자 초기화 실패: {e}")
    # 폴백 처리
```

### Flask 라우트 스타일
```python
@app.route('/api/endpoint', methods=['POST'])
def endpoint_handler():
    """API 엔드포인트 핸들러"""
    try:
        # 처리 로직
        return jsonify({
            'success': True,
            'data': result,
            'message': '성공'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 로깅 스타일
```python
app.logger.info("정보 로그")
app.logger.error(f"에러 발생: {str(e)}")
app.logger.debug(f"디버그: {variable}")
```

## 파일 구조 규칙

### Import 순서
1. 표준 라이브러리
2. 서드파티 라이브러리
3. 로컬 모듈

```python
import os
from pathlib import Path

from flask import Flask, jsonify
from reportlab.lib import colors

from src.core.settings_manager import get_settings_manager
```

### 파일 헤더
```python
"""
파일 설명 및 목적
간단한 모듈 설명
"""
```

## 데이터베이스 규칙

### 테이블 명명
- snake_case 사용
- 복수형 사용: `emails`, `attachments`, `settings`

### 컬럼 명명
- snake_case 사용
- 명확한 이름: `created_at`, `deleted_at`, `is_deleted`
