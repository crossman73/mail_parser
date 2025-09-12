# 이메일 증거 처리 시스템 개발자 가이드 🚀

> **자동 생성된 개발자 문서** | 마지막 업데이트: 2025-09-03 15:23:01

## 📊 프로젝트 현황

- **총 엔드포인트**: 62개
- **웹 라우트**: 38개
- **팩토리 라우트**: 6개
- **API 라우트**: 18개
- **데이터 모델**: 1개

## 🚀 빠른 시작

### 설치 및 실행

```bash
# 1. 저장소 클론
git clone [repository-url]
cd python-email

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 시작
python app.py
# 또는
python main.py --web
```

### 개발 서버

```bash
# 개발 모드로 시작 (자동 재시작)
FLASK_ENV=development python app.py

# 특정 포트로 시작
python main.py --web --port 8080

# 시스템 테스트
python main.py --test
```

## 🏗️ 프로젝트 구조

```
python-email/
├── src/                    # 소스 코드
│   ├── core/               # 핵심 비즈니스 로직
│   │   └── unified_architecture.py  # 통합 아키텍처
│   ├── docs/               # 문서 생성 시스템
│   │   ├── api_scanner.py  # API 자동 스캔
│   │   └── doc_generator.py # 문서 자동 생성
│   ├── mail_parser/        # 이메일 처리 엔진
│   └── web/                # 웹 인터페이스
│       ├── routes.py       # 웹 라우트
│       └── app_factory.py  # Flask 팩토리
├── templates/              # HTML 템플릿
├── static/                 # 정적 파일
├── docs/                   # 문서 (자동 생성)
└── tests/                  # 테스트
```

## 🔧 개발 환경 설정

### Phase 1 - 통합 아키텍처

```bash
# Phase 1 검증
python test_phase1.py

# 시스템 상태 확인
python main.py --test
```

### Phase 2 - API 문서 자동화

```bash
# API 스캔 및 문서 생성
python -c "from src.docs import generate_all_documentation; generate_all_documentation()"

# 개별 문서 생성 테스트
python test_docs_generation.py
```

## 🧪 테스트

### 단위 테스트 실행

```bash
# Phase 1 테스트
python test_phase1.py

# 전체 시스템 테스트
python main.py --test

# 문서 생성 테스트
python test_docs_generation.py
```

## 📝 코딩 스타일

### Python 스타일 가이드

- PEP 8 준수
- Type hints 사용 권장
- Docstring 필수 (Google 스타일)

```python
def process_email(email_path: str, party: str = "갑") -> Dict[str, Any]:
    '''이메일 처리 함수

    Args:
        email_path: 이메일 파일 경로
        party: 당사자 구분 (갑/을)

    Returns:
        처리 결과 딕셔너리

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
    '''
    pass
```

## 🔌 API 개발

### 새 API 엔드포인트 추가

1. 적절한 파일에 라우트 추가 (app_factory.py, routes.py 등)
2. 적절한 HTTP 상태 코드 사용
3. JSON 응답 형식 일관성 유지

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    '''새 API 엔드포인트'''
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

### 자동 문서화

새로운 API를 추가하면 자동으로 문서가 업데이트됩니다:

1. **API 스캔**: `APIScanner`가 자동으로 새 엔드포인트 감지
2. **문서 생성**: `DocumentGenerator`가 마크다운, HTML, OpenAPI 명세 생성
3. **문서 배포**: `docs/` 폴더에 자동 저장

## 📚 문서 시스템

### 자동 생성되는 문서

- **API_Reference.md**: 전체 API 레퍼런스
- **api_docs.html**: 웹용 HTML 문서
- **openapi.json**: OpenAPI 3.0 명세
- **Developer_Guide.md**: 개발자 가이드 (이 파일)
- **postman_collection.json**: Postman 테스트 컬렉션

### 문서 재생성

```bash
# 전체 문서 재생성
python -c "from src.docs import generate_all_documentation; generate_all_documentation()"
```

## 🚀 배포

### 프로덕션 배포

```bash
# Docker로 프로덕션 배포
docker-compose up -d

# 직접 배포
gunicorn -w 4 -b 0.0.0.0:5000 'src.web.app:create_app()'
```

## 📚 추가 리소스

- [API Reference](API_Reference.md) - 전체 API 문서
- [설정 가이드](config_guide.md) - 설정 가이드 (생성 예정)
- [아키텍처 문서](architecture_refactoring.md) - 아키텍처 문서 (생성 예정)

---

**이 문서는 자동으로 생성되었습니다.** Phase 2 API 문서 자동화 시스템이 프로젝트를 스캔하여 실시간으로 업데이트합니다.
