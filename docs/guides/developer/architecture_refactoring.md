# 프로젝트 아키텍처 정리

## 📁 표준화된 디렉토리 구조

```
python-email/
├── main.py                      # 메인 CLI 진입점
├── web_app.py                   # 웹 애플리케이션 진입점
├── config.json                  # 기본 설정 파일
├── requirements.txt             # Python 의존성
├── README.md                    # 프로젝트 문서
│
├── src/                         # 소스 코드
│   ├── __init__.py
│   ├── core/                    # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── processor.py         # 메일 처리 핵심 로직
│   │   ├── analyzer.py          # 메일 분석
│   │   ├── formatter.py         # 증거 형식 변환
│   │   ├── integrity.py         # 무결성 관리
│   │   └── utils.py            # 공통 유틸리티
│   │
│   ├── services/               # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── mail_service.py     # 메일 처리 서비스
│   │   ├── evidence_service.py # 증거 생성 서비스
│   │   ├── timeline_service.py # 타임라인 서비스
│   │   └── export_service.py   # 내보내기 서비스
│   │
│   ├── web/                    # 웹 인터페이스
│   │   ├── __init__.py
│   │   ├── app.py             # Flask 애플리케이션
│   │   ├── routes/            # 라우팅
│   │   │   ├── __init__.py
│   │   │   ├── main.py        # 메인 페이지
│   │   │   ├── upload.py      # 파일 업로드
│   │   │   ├── timeline.py    # 타임라인
│   │   │   └── evidence.py    # 증거 관리
│   │   └── api/              # REST API
│   │       ├── __init__.py
│   │       ├── mails.py       # 메일 API
│   │       └── evidence.py    # 증거 API
│   │
│   ├── models/                # 데이터 모델
│   │   ├── __init__.py
│   │   ├── mail.py           # 메일 데이터 모델
│   │   ├── evidence.py       # 증거 데이터 모델
│   │   └── timeline.py       # 타임라인 모델
│   │
│   └── utils/                # 유틸리티
│       ├── __init__.py
│       ├── logger.py         # 로깅
│       ├── progress.py       # 진행률 표시
│       ├── performance.py    # 성능 모니터링
│       └── packaging.py      # 패키징
│
├── templates/                # 웹 템플릿
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── timeline.html
│   └── evidence.html
│
├── static/                   # 정적 파일
│   ├── css/
│   ├── js/
│   └── images/
│
├── tests/                    # 테스트
│   ├── __init__.py
│   ├── test_core/
│   ├── test_services/
│   └── test_web/
│
├── data/                     # 데이터 디렉토리
│   ├── uploads/             # 업로드된 mbox 파일
│   ├── processed/           # 처리된 메일
│   ├── evidence/           # 생성된 증거물
│   └── exports/            # 내보낸 패키지
│
├── logs/                    # 로그 파일
├── config/                  # 추가 설정 파일
└── docs/                   # 문서
```

## 🔧 리팩토링 계획

### Phase 1: 핵심 모듈 이동 및 정리
1. mail_parser → core로 이동
2. 중복 파일 정리
3. 의존성 정리

### Phase 2: 서비스 레이어 구성
1. 비즈니스 로직을 서비스로 분리
2. API 인터페이스 표준화

### Phase 3: 웹 인터페이스 통합
1. 분산된 웹 파일들 통합
2. 라우팅 구조화

### Phase 4: 데이터 모델 정의
1. 표준 데이터 클래스 정의
2. 타입 힌트 적용
