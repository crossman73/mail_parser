# 자주 사용하는 명령어

## 서버 실행

### 메인 웹 서버 (권장)
```powershell
# 가상환경 활성화
& c:/dev/python-email/.venv/Scripts/Activate.ps1

# 웹서버 실행
python -m src.web.app

# 또는 runner 사용
python src/runner/run_server.py
```

### 백그라운드 실행
```powershell
Start-Process python -ArgumentList "-m", "src.web.app" -WindowStyle Hidden
```

## 개발 환경

### 가상환경
```powershell
# 활성화
& .venv/Scripts/Activate.ps1

# 비활성화
deactivate
```

### 패키지 관리
```powershell
# 패키지 목록 확인
python -m pip list

# 특정 패키지 확인
python -m pip show Flask

# 패키지 설치 (필요시)
python -m pip install <package_name>
```

## 데이터베이스

### DB 확인
```powershell
# DB 파일 존재 확인
Test-Path data/db/email_parser.db

# DB 크기 확인
Get-Item data/db/email_parser.db | Select-Object Length, LastWriteTime
```

## 로그 확인

### 로그 파일
```powershell
# 최신 로그 파일 확인
Get-ChildItem logs/*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# 로그 내용 보기
Get-Content logs/mail_parser_*.log -Tail 50
```

## 파일 관리

### 디렉터리 구조
```powershell
# 프로젝트 구조 확인
tree /F

# 특정 디렉터리 내용
Get-ChildItem -Recurse src/ -Directory
```

### 파일 검색
```powershell
# Python 파일 검색
Get-ChildItem -Recurse -Filter *.py

# 특정 파일 찾기
Get-ChildItem -Recurse -Include "app.py","routes.py"
```

## Git 명령어

### 상태 확인
```powershell
# 현재 상태
git status

# 브랜치 확인
git branch

# 변경 내역
git log --oneline --graph -5
```

### 커밋 & 푸시
```powershell
# 변경 파일 추가
git add .

# 커밋
git commit -m "feat: 기능 추가"

# 푸시
git push origin <branch_name>
```

## 시스템 명령어 (Windows)

### 프로세스 관리
```powershell
# Python 프로세스 확인
Get-Process python

# 포트 사용 확인
netstat -ano | findstr :5000

# 프로세스 종료
Stop-Process -Id <PID>
```

### 네트워크
```powershell
# 서버 접속 테스트
curl http://localhost:5000

# 상세 테스트
Invoke-WebRequest http://localhost:5000 -UseBasicParsing
```

## MCP Serena 명령어

### 프로젝트 활성화
```
mcp_serena_activate_project("c:\\dev\\python-email")
```

### 파일 검색
```
mcp_serena_find_file("app.py", "src")
mcp_serena_search_for_pattern("def create_app", "src/web")
```

### 심볼 검색
```
mcp_serena_get_symbols_overview("src/web/app.py")
mcp_serena_find_symbol("create_app", "src/web/app.py")
```
