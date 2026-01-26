# 프로젝트 개요

## 프로젝트 목적
**court-evidence-system** - 법원 증거 관리 시스템
- 이메일 증거 처리, 무결성 검증, 타임라인 분석 및 법적 규정 준수 기능을 제공하는 웹 기반 시스템
- 한국 법원 제출용 이메일 증거 자동 생성 및 처리

## 주요 기능
- 📧 mbox/eml 파일 자동 파싱 (Outlook, Thunderbird 지원)
- ⚖️ 법정 증거 자동 생성 (한국 법원 규정 준수)
- 📊 타임라인 시각화 (이메일 송수신 흐름)
- 🔒 무결성 검증 (SHA-256 해시 기반)
- 🌐 웹 인터페이스 (직관적인 UI)
- 📚 자동 문서화 (API 스캔 기반)

## 기술 스택
- **Backend**: Python 3.13.9, Flask 3.1.2
- **Database**: SQLite (email_parser.db)
- **Frontend**: Bootstrap 5.1.3, Font Awesome 6.0.0 ✅ (통일 완료), Google Fonts (Inter)
- **Custom Assets**:
  - modern-ui.css (CSS 변수, 다크모드, 반응형)
  - common.js (다크모드 토글, 유틸리티)
- **라이브러리**:
  - reportlab (PDF 생성)
  - openpyxl (Excel 생성)
  - beautifulsoup4 (HTML 파싱)
  - psutil (시스템 모니터링)
  - watchdog (파일 변경 감지)
- **MCP Servers**:
  - Serena (심볼릭 코드 분석)
  - GitHub (코드 검색, 이슈 관리)
  - Desktop Commander (파일 시스템 작업)
  - Brave Search (웹 검색)
  - Codacy (코드 품질 분석)

## 프로젝트 구조
```
python-email/
├── src/                    # 소스 코드
│   ├── core/               # 핵심 비즈니스 로직
│   │   ├── settings_manager.py  # 설정 관리
│   │   └── unified_architecture.py  # 통합 아키텍처
│   ├── web/                # 웹 애플리케이션
│   │   ├── app.py          # Flask 앱 (메인)
│   │   ├── app_factory.py  # Flask 팩토리
│   │   ├── routes.py       # 웹 라우트
│   │   ├── api.py          # API 라우트
│   │   └── admin_routes.py # 관리자 라우트
│   ├── mail_parser/        # 이메일 처리 엔진
│   ├── utils/              # 유틸리티
│   │   ├── db_logger.py    # DB 로깅
│   │   └── unified_logger.py  # 통합 로거
│   └── runner/             # 실행 스크립트
├── templates/              # HTML 템플릿
├── static/                 # 정적 파일 (CSS, JS)
├── data/db/                # 데이터베이스 파일
├── uploads/                # 업로드 파일
├── logs/                   # 로그 파일
└── tests/                  # 테스트
```

## 환경 설정
- **Python 가상환경**: `.venv/` (Python 3.13.9)
- **데이터베이스**: `data/db/email_parser.db`
- **업로드 폴더**: `uploads/`
- **로그 폴더**: `logs/`
- **정적 파일**: `static/` (현재 비어있음 - CSS/JS 필요)
