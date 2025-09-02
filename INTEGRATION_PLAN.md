# 메일 파서 아키텍처 통합 및 정리

## 현재 상태 (2025-09-01)

### 🚨 문제점 분석
1. **중복 파일들**: app.py, app_server.py, timeline_server.py 등 여러 웹 서버 파일
2. **분산된 구조**: src/mail_parser, src/core, src/web_app, src/web_interface 등 복잡한 구조
3. **메모리 효율성**: 불필요한 파일 생성으로 인한 성능 저하

### 📋 통합 계획

#### Phase 1: 파일 정리 및 통합
- [ ] 중복 웹 서버 파일 통합 (app.py 하나로 통일)
- [ ] 불필요한 디렉토리 제거
- [ ] core 모듈을 mail_parser에 통합

#### Phase 2: 메인 구조 정리
```
python-email/
├── main.py              # 메인 진입점
├── config.json         # 설정 파일
├── requirements.txt    # 의존성
├── src/
│   └── mail_parser/    # 통합된 메인 모듈
│       ├── __init__.py
│       ├── models/     # 데이터 모델
│       ├── services/   # 비즈니스 로직
│       ├── utils/      # 유틸리티
│       └── web/        # 웹 인터페이스
├── tests/              # 테스트 파일
├── docs/               # 문서
└── processed_emails/   # 출력 폴더
```

### 🎯 즉시 실행 계획

1. **중복 파일 정리**: 여러 app*.py 파일을 하나로 통합
2. **디렉토리 정리**: src/core를 src/mail_parser로 이동
3. **설정 파일 통합**: 하나의 config.json으로 관리
4. **문서 정리**: 진행 상황을 하나의 파일로 통합

### 🔧 실행 중단점
- IDE 재시작 시에도 지속 가능한 구조
- 메모리 효율성 최우선
- 파일 개수 최소화

## 다음 단계
1. 중복 파일 제거 및 통합
2. 디렉토리 구조 단순화
3. 설정 및 문서 정리
4. 테스트 및 검증
