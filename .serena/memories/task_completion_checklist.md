# 작업 완료 시 체크리스트

## 코드 작성 후

### 1. 코드 품질 확인
- [ ] PEP 8 스타일 준수
- [ ] Docstring 작성 완료
- [ ] Type hints 추가 (권장)
- [ ] 한글 주석/메시지 적절성 확인

### 2. 에러 처리
- [ ] try-except 블록 추가
- [ ] 적절한 에러 메시지
- [ ] 로깅 추가 (app.logger 사용)

### 3. 테스트
- [ ] 로컬 서버 실행 테스트
```powershell
python -m src.web.app
```
- [ ] 웹 브라우저 접속 확인 (http://localhost:5000)
- [ ] 주요 기능 동작 확인

### 4. 데이터베이스
- [ ] DB 파일 존재 확인
```powershell
Test-Path data/db/email_parser.db
```
- [ ] DB 연결 성공 메시지 확인

### 5. 로그 확인
- [ ] 로그 디렉터리 존재
- [ ] 에러 로그 없음
```powershell
Get-ChildItem logs/*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

## Git 커밋 전

### 1. 변경사항 확인
```powershell
git status
git diff
```

### 2. 불필요한 파일 제외
- __pycache__/
- *.pyc
- .venv/
- logs/
- data/db/*.db
- uploads/
- temp/

### 3. 커밋 메시지 작성
Conventional Commits 형식 사용:
```
feat: 새 기능 추가
fix: 버그 수정
chore: 설정 변경
docs: 문서 수정
refactor: 코드 리팩토링
style: 코드 스타일 수정
test: 테스트 추가
```

예시:
```powershell
git add .
git commit -m "feat: 설정 관리 UI 추가

- 날짜 포맷 설정 기능
- 툴팁 표시 설정
- 민감정보 마스킹 옵션

작업 시간: 2025-12-29"
```

### 4. 푸시 전 확인
- [ ] 브랜치 확인
```powershell
git branch
```
- [ ] 원격 저장소 확인
```powershell
git remote -v
```
- [ ] 푸시
```powershell
git push origin <branch_name>
```

## 배포 전

### 1. 환경 변수 확인
- SECRET_KEY 설정
- FLASK_ENV 설정 (development/production)
- 데이터베이스 경로 확인

### 2. 의존성 확인
필수 패키지 설치 여부:
- Flask
- reportlab
- openpyxl
- psutil
- watchdog

### 3. 디렉터리 구조
필수 디렉터리 존재 확인:
- data/db/
- uploads/
- logs/
- static/css/
- static/js/
- templates/

### 4. 정적 파일
- CSS 파일 존재 확인 (static/css/)
- JS 파일 존재 확인 (static/js/)
- 404 에러 없음

## 문서화

### API 변경 시
- [ ] API 엔드포인트 문서화
- [ ] 요청/응답 예시 작성
- [ ] 에러 코드 정의

### 주요 기능 추가 시
- [ ] README.md 업데이트
- [ ] 사용 방법 문서 작성
- [ ] 스크린샷/예시 추가

## MCP Serena 사용 시

### 메모리 업데이트
주요 변경 사항을 메모리에 저장:
```
mcp_serena_write_memory("memory_file_name.md", "내용")
```

### 심볼 검증
변경된 함수/클래스 확인:
```
mcp_serena_get_symbols_overview("파일경로")
mcp_serena_find_symbol("심볼명", "파일경로")
```
