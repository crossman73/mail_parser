# Court Evidence System (법원 증거 관리 시스템)

이메일(.mbox) 파일을 법적 증거로 변환하고, 무결성 검증(해시 체인), 타임라인 분석, 법적 규정 준수 기능을 제공하는 Flask 기반 웹 시스템입니다.

## 주요 기능

- **이메일 증거 처리**: mbox 파일 파싱, 스레드 그룹핑, 첨부파일 추출
- **무결성 검증**: SHA-256 해시 체인으로 증거 위변조 방지
- **타임라인 분석**: 이메일 흐름을 시간순 타임라인으로 시각화
- **법적 규정 준수**: 한국 법원 디지털 증거 제출 규정 준수 검증
- **관리자 대시보드**: 시스템 상태, 로그, 설정 관리

## 빠른 시작 (WSL)

```bash
# 환경 구축
bash tools/setup_wsl_env.sh

# 가상환경 활성화
source .venv/bin/activate

# 서버 실행
python src/runner/run_server.py
```

접속: http://localhost:5000

## 프로젝트 구조

```
src/
├── web/           # Flask 앱, 라우트, 블루프린트
├── mail_parser/   # 이메일 파싱 핵심 로직
├── core/          # DB, 설정, 유틸, 서비스 공통 인프라
├── evidence/      # 추가 증거 관리
├── timeline/      # 타임라인 생성
├── services/      # 비즈니스 로직 서비스
├── database/      # DB 모델, 마이그레이션
└── runner/        # 서버 실행 스크립트
```

## 기술 스택

- **Backend**: Python 3.12, Flask 3.x
- **Frontend**: Bootstrap 5, Font Awesome, 다크모드 지원
- **Database**: SQLite
- **Environment**: WSL Ubuntu

## 문서

- [아키텍처](docs/ARCHITECTURE.md)
- [API 레퍼런스](docs/API_REFERENCE.md)
- [라우팅 맵](docs/ROUTING_MAP.md)
- [시스템 테스트](docs/SYSTEM_TESTS.md)

## 라이선스

MIT License
