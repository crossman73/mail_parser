# 프로젝트 동기화 가이드

> 다른 머신에서 이 프로젝트를 클론하여 개발을 이어가기 위한 가이드

## 빠른 시작

```bash
# 1. 클론
git clone -b feature/admin-settings-clean https://github.com/crossman73/mail_parser.git
cd mail_parser

# 2. WSL 환경 구축 (의존성 전체 설치)
bash tools/setup_wsl_env.sh

# 3. venv 활성화
source .venv/bin/activate

# 4. 개발 서버 실행
python -m src.runner.run_server
# → http://localhost:5000
```

## 포함된 데이터

| 파일 | 설명 |
|------|------|
| `data/db/email_parser.db` | 통합 SQLite DB (20+ 테이블) |
| `data/db/schema_dump.sql` | DB 스키마 덤프 (참조용) |

- DB 파일은 `.gitignore` 예외 처리(`!data/db/email_parser.db`)로 Git 추적됨
- 클론 즉시 DB 사용 가능, 별도 마이그레이션 불필요

## 환경 요구사항

- **Python**: 3.12+
- **OS**: WSL Ubuntu 권장 (Windows에서도 동작)
- **주요 패키지**: Flask 3.x, python-pptx, python-docx, Pillow

## DB 스키마 재생성 (필요 시)

```bash
# DB 파일 없이 스키마만으로 빈 DB 생성
source .venv/bin/activate
python -c "
import sqlite3
with open('data/db/schema_dump.sql') as f:
    sql = f.read()
conn = sqlite3.connect('data/db/email_parser.db')
conn.executescript(sql)
conn.close()
print('DB 생성 완료')
"
```

## VS Code 설정

- `.vscode/settings.json`, `.vscode/tasks.json`, `.vscode/mcp.json` 포함
- VS Code 열면 자동 적용
- MCP 서버(Serena, Codacy, Context7 등) 설정 포함

## 현재 개발 상태 (Phase 0-7 완료)

| Phase | 내용 | 상태 |
|-------|------|------|
| 0 | DB 통합 (5테이블, 4스토어) | ✅ |
| 1 | 모델 리팩토링 | ✅ |
| 2 | Service 레이어 CRUD | ✅ |
| 3 | REST API (12 엔드포인트) | ✅ |
| 4 | Export (PPT/Word/HTML) | ✅ |
| 5 | UI 편집기 (SortableJS) | ✅ |
| 6 | 이메일→타임라인 스트리밍 | ✅ |
| 7 | Hash chain 무결성 | ✅ |

## 테스트

```bash
# E2E 테스트 (23항목)
python -m pytest tests/ -q

# 개발 서버로 수동 테스트
python -m src.runner.run_server
# 타임라인 편집기: http://localhost:5000/timeline_editor
```
