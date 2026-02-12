# VS Code 환경 구성 가이드

이 문서는 `mail_parser` 프로젝트의 VS Code 개발 환경을 WSL Ubuntu에서 구성하는 방법을 설명합니다.

## 📋 사전 요구사항

### 필수 소프트웨어

| 소프트웨어 | 최소 버전 | 설치 명령 (WSL Ubuntu) |
|-----------|----------|----------------------|
| Python | 3.12+ | `sudo apt install python3.12 python3.12-venv` |
| Node.js | v20+ | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo -E bash - && sudo apt install nodejs` |
| Git | 2.40+ | `sudo apt install git` |

### 버전 확인
```bash
python3 --version  # Python 3.12.x
node --version     # v20.x.x
npm --version      # 10.x.x
git --version      # git version 2.x
```

---

## 🚀 빠른 설정 (자동화)

### 1. 프로젝트 클론
```bash
git clone https://github.com/crossman73/mail_parser.git
cd mail_parser
```

### 2. 환경 자동 설정
```bash
# 전체 환경 구축 (Python, Node, 의존성 모두)
bash tools/setup_wsl_env.sh
```

### 3. 수동 설정 (선택)
```bash
# Python 가상환경
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Node 의존성 (필요시)
npm install
```

### 4. VS Code 열기
```bash
code .
```

---

## 📦 VS Code 확장 프로그램

### 필수 확장 (Core)
```
github.copilot                    # GitHub Copilot
github.copilot-chat               # GitHub Copilot Chat
ms-python.python                  # Python
ms-python.vscode-pylance          # Pylance
codacy-app.codacy                 # Codacy 코드 품질
```

### Python 개발
```
ms-python.debugpy                 # Python 디버거
ms-python.black-formatter         # Black 포매터
ms-python.isort                   # Import 정렬
ms-python.autopep8                # AutoPEP8
donjayamanne.python-extension-pack # Python 확장 팩
kevinrose.vsc-python-indent       # Python 들여쓰기
njpwerner.autodocstring           # 자동 docstring
```

### 웹 개발
```
ecmel.vscode-html-css             # HTML/CSS 지원
pranaygp.vscode-css-peek          # CSS Peek
bradlc.vscode-tailwindcss         # Tailwind CSS
esbenp.prettier-vscode            # Prettier
dbaeumer.vscode-eslint            # ESLint
```

### Git & GitHub
```
github.vscode-pull-request-github # GitHub PR
github.vscode-github-actions      # GitHub Actions
```

### 컨테이너 & 원격
```
ms-azuretools.vscode-docker       # Docker
ms-vscode-remote.remote-containers # Dev Containers
ms-vscode-remote.remote-ssh       # Remote SSH
ms-vscode-remote.remote-wsl       # WSL
```

### 생산성
```
aaron-bond.better-comments        # 향상된 주석
usernamehw.errorlens              # 인라인 에러 표시
wayou.vscode-todo-highlight       # TODO 하이라이트
humao.rest-client                 # REST Client
rangav.vscode-thunder-client      # Thunder Client (API 테스트)
```

### 마크다운 & 문서
```
yzhang.markdown-all-in-one        # Markdown All in One
davidanson.vscode-markdownlint    # Markdown Lint
shd101wyy.markdown-preview-enhanced # Markdown 미리보기
bierner.markdown-mermaid          # Mermaid 다이어그램
```

### 테마 & UI
```
azemoh.one-monokai                # One Monokai 테마
pkief.material-icon-theme         # Material 아이콘
naumovs.color-highlight           # 색상 하이라이트
```

### 한국어 지원
```
ms-ceintl.vscode-language-pack-ko # 한국어 팩
dinner.korean-translator          # 한국어 번역
yunseok.korean-spell-checker-vs-code # 한국어 맞춤법
```

---

## ⚙️ VS Code 설정 (settings.json)

### 사용자 설정 위치
- **Windows**: `%APPDATA%\Code\User\settings.json`
- **macOS**: `~/Library/Application Support/Code/User/settings.json`
- **Linux**: `~/.config/Code/User/settings.json`

### 권장 설정
```json
{
  "files.autoSave": "afterDelay",
  "editor.tabSize": 2,
  "editor.formatOnSave": true,
  "editor.formatOnSaveMode": "modifications",
  "editor.wordWrap": "on",
  "editor.stickyScroll.enabled": true,
  "workbench.colorTheme": "One Monokai",
  "workbench.startupEditor": "none",
  "git.autofetch": true,
  "python.analysis.typeCheckingMode": "strict",
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "github.copilot.nextEditSuggestions.enabled": true,
  "chat.mcp.gallery.enabled": true,
  "codacy.cli.devMode": true,
  "security.workspace.trust.untrustedFiles": "open",
  "redhat.telemetry.enabled": true
}
```

---

## 🔌 MCP 서버 설정

MCP 설정은 `.vscode/mcp.json`에 프로젝트별로 저장됩니다 (Git에 포함됨).

### 환경 변수 설정 (필수)

#### BRAVE_API_KEY 설정
```powershell
# 사용자 환경 변수로 설정
[Environment]::SetEnvironmentVariable('BRAVE_API_KEY', 'your-api-key', 'User')

# 또는 VS Code 태스크 사용
# Ctrl+Shift+P → Tasks: Run Task → Set BRAVE_API_KEY (User)
```

### MCP 서버 목록
| 서버 | 용도 | 우선순위 |
|-----|------|---------|
| codacy | 코드 품질 분석 | 🔴 필수 |
| serena | 코드 구조/심볼 분석 | 🔴 필수 |
| context7 | 컨텍스트 관리 | 🟡 권장 |
| brave-search | 웹 검색 | 🟡 권장 |
| sequential-thinking | 단계적 사고 | 🟢 선택 |
| playwright | 브라우저 자동화 | 🟢 선택 |
| memory | 메모리 관리 | 🟢 선택 |

---

## 🔧 문제 해결

### MCP 서버가 시작되지 않을 때
1. VS Code 완전 재시작
2. `Ctrl+Shift+P` → "MCP: List Servers" → 서버 상태 확인
3. Output 패널에서 MCP 로그 확인

### Serena 프로젝트 활성화
VS Code 재시작 후 Copilot Chat에서:
```
Serena 프로젝트를 c:\dev\python-email로 활성화해줘
```

### Python 환경 문제
```powershell
# 가상환경 재생성
Remove-Item -Recurse -Force .venv
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

---

## 📁 프로젝트 구조 (참고)

```
mail_parser/
├── .github/instructions/    # Copilot 지시사항
├── .vscode/
│   ├── mcp.json            # MCP 서버 설정
│   ├── settings.json       # 워크스페이스 설정
│   └── tasks.json          # 태스크 정의
├── docs/                   # 문서
├── src/                    # 소스 코드
├── static/                 # 정적 파일
├── templates/              # Jinja2 템플릿
├── tests/                  # 테스트
└── tools/                  # 유틸리티 스크립트
```

---

_최종 업데이트: 2026-01-12_
