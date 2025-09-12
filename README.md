# 이메일 증거 처리 시스템 📧

> 한국 법원 제출용 이메일 증거 처리 및 분류 시스템 v2.0

## 🎯 주요 기능

- 📧 **mbox/eml 파일 자동 파싱**: Outlook, Thunderbird 등 다양한 메일 클라이언트 지원
- ⚖️ **법정 증거 자동 생성**: 한국 법원 규정에 맞는 증거 번호 및 형식 자동 적용
- 📊 **타임라인 시각화**: 이메일 송수신 흐름을 직관적인 타임라인으로 표시
- 🔒 **무결성 검증**: SHA-256 해시값 기반 디지털 증거 무결성 보장
- 🌐 **웹 인터페이스**: 직관적인 웹 UI로 누구나 쉽게 사용 가능
- 📚 **자동 문서화**: API 스캔을 통한 실시간 문서 생성

## 📊 시스템 현황

- **총 엔드포인트**: 73개
- **웹 라우트**: 47개
- **팩토리 라우트**: 8개
- **API 라우트**: 18개
- **데이터 모델**: 1개

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone [repository-url]
cd python-email

# 의존성 설치
pip install -r requirements.txt
```

### 2. 실행

```bash
# 웹 서버 시작
python app.py

# CLI 모드 (mbox 파일 직접 처리)
python main.py email_files/sample.mbox --party 갑

# Docker로 실행
docker-compose up -d
```

### 3. 접속

- **웹 인터페이스**: http://localhost:5000
- **API 문서**: http://localhost:5000/docs
- **시스템 상태**: http://localhost:5000/system/status
- **헬스체크**: http://localhost:5000/health

## 📋 사용법

### 웹 인터페이스 사용

1. **파일 업로드**: mbox 또는 eml 파일을 업로드
2. **이메일 선택**: 증거로 사용할 이메일들 선택
3. **증거 생성**: 당사자 구분(갑/을) 설정 후 증거 자동 생성
4. **결과 다운로드**: PDF, HTML, Excel 형식으로 다운로드

### CLI 사용

```bash
# 기본 사용법
python main.py [mbox파일] --party [갑|을]

# 웹 서버 모드
python main.py --web --port 8080

# 시스템 테스트
python main.py --test

# Phase 1 검증
python test_phase1.py
```

## 🏗️ 아키텍처

### Phase 1: 통합 아키텍처 ✅
- **SystemConfig**: 중앙 집중식 설정 관리
- **UnifiedArchitecture**: 서비스 레지스트리 패턴
- **Flask Factory**: 모듈화된 웹 애플리케이션

### Phase 2: API 문서 자동화 ✅
- **APIScanner**: 코드 자동 스캔 및 분석
- **DocumentGenerator**: 다양한 형식 문서 생성
- **실시간 문서화**: 코드 변경 시 자동 업데이트

### Phase 3: 백그라운드 서비스 (구현 예정)
- 터미널 블록 없는 서비스 실행
- 로그 모니터링 시스템
- 서비스 상태 관리

## 🔧 설정

### config.json 주요 설정

```json
{
  "exclude_keywords": ["광고", "스팸"],
  "date_range": {
    "start": "2020-01-01",
    "end": "2025-12-31"
  },
  "processing_options": {
    "generate_hash_verification": true,
    "create_backup": true
  },
  "output_settings": {
    "evidence_number_format": "{party} 제{number}호증"
  }
}
```

## 🧪 테스트

```bash
# Phase 1 검증
python test_phase1.py

# Phase 2 문서 생성 테스트
python test_docs_generation.py

# 시스템 전체 테스트
python main.py --test
```

## 📚 문서

**자동 생성된 문서들**:
- [📖 API Reference](docs/API_Reference.md) - 전체 API 문서
- [🔧 Developer Guide](docs/Developer_Guide.md) - 개발자 가이드
- [🌐 HTML 문서](docs/api_docs.html) - 웹용 API 문서
- [🔌 OpenAPI 명세](docs/openapi.json) - OpenAPI 3.0 스펙
- [📮 Postman Collection](docs/postman_collection.json) - API 테스트 컬렉션

**수동 문서들**:
- [⚙️ Config Guide](docs/config_guide.md) - 설정 가이드 (생성 예정)
- [🏗️ Architecture](docs/architecture_refactoring.md) - 아키텍처 문서

## 🐳 Docker 지원

```bash
# 개발 환경
docker-compose -f docker-compose.dev.yml up

# 프로덕션 환경
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

## 🔌 API 엔드포인트

현재 발견된 엔드포인트 (73개):

**주요 엔드포인트**:
- `GET /` - 메인 페이지
- `GET /health` - 시스템 헬스체크
- `GET /system/status` - 시스템 상태 정보
- `GET /docs` - API 문서 페이지
- `GET /upload` - 파일 업로드 페이지 (구현 예정)

자세한 API 문서는 [API Reference](docs/API_Reference.md)를 참고하세요.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다.

---

**마지막 업데이트**: 2025-09-05 17:41:50
**문서 자동 생성**: Phase 2 API 문서 생성 시스템
**문서 버전**: v2.0 (통합 아키텍처 + 자동 문서화)
