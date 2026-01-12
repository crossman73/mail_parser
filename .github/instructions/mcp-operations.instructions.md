---
description: MCP 서버 운영 및 최적화 가이드 (MLOps 관점)
applyTo: "**"
---

# MCP 서버 운영 가이드

## 🎯 목표

- VS Code 안정성 유지
- MCP 서버 최적 활용
- MLOps 관점의 체계적 관리

---

## 📊 현재 MCP 서버 구성

### 워크스페이스 MCP 서버 (`.vscode/mcp.json`)

| 서버                  | 용도                                | 우선순위 |
| --------------------- | ----------------------------------- | -------- |
| `codacy`              | 코드 품질 분석                      | 🔴 필수  |
| `serena`              | 코드 구조 분석, 심볼 검색, 리팩토링 | 🔴 필수  |
| `context7`            | 컨텍스트 관리                       | 🟡 권장  |
| `brave-search`        | 웹 검색                             | 🟡 권장  |
| `sequential-thinking` | 단계적 사고                         | 🟢 선택  |
| `playwright`          | 브라우저 자동화                     | 🟢 선택  |
| `memory`              | 메모리 관리                         | 🟢 선택  |
| `desktop-commander`   | 데스크톱 제어                       | 🟢 선택  |
| `markitdown`          | 마크다운 변환                       | 🟢 선택  |

### VS Code 사용자 MCP 서버 (`settings.json`)

| 서버     | 용도               | 상태             |
| -------- | ------------------ | ---------------- |
| `github` | GitHub Copilot MCP | autostart: false |
| `fetch`  | HTTP 요청          | autostart: false |

---

## ⚙️ 안정성 설정

### 필수 설정 값

```json
{
  "mcp.server.autoStart": true,
  "mcp.server.maxTools": 128,
  "chat.mcp.discovery.enabled": false,
  "chat.mcp.autostart": "afterDelay",
  "mcp.logLevel": "error"
}
```

### 안정성 체크리스트

- [ ] `chat.mcp.discovery.enabled`: false (외부 앱 검색 비활성화)
- [ ] `mcp.logLevel`: "error" (불필요한 로그 감소)
- [ ] `chat.agent.maxRequests`: 30 (과부하 방지)

---

## 🔧 문제 해결

### "client not ready" 에러

1. VS Code 완전 재시작
2. MCP 캐시 초기화: `MCP: 캐시된 도구 다시 설정`
3. 특정 서버만 비활성화 테스트

### MCP 서버 충돌

1. 중복 서버 확인 (VS Code + Claude Desktop)
2. `autostart: false`로 수동 시작 전환
3. 로그 레벨을 "debug"로 변경하여 원인 파악

### 성능 저하

1. 사용하지 않는 MCP 서버 비활성화
2. `mcp.server.maxTools` 값 조정
3. 메모리 사용량 모니터링

---

## 📈 MLOps 운영 지침

### 모니터링

- VS Code 개발자 도구 콘솔 확인
- MCP 서버 응답 시간 체크
- 메모리 사용량 추적

### 배포 전 체크리스트

- [ ] 모든 MCP 서버 정상 동작 확인
- [ ] Codacy 분석 통과
- [ ] 테스트 실행 완료

### 버전 관리

- `.vscode/mcp.json`: Git 추적 (팀 공유)
- 사용자 `settings.json`: 개인 설정 (Git 제외)

---

## 🚀 MCP 서버 사용 가이드

### Codacy (필수)

```
@codacy analyze   # 코드 분석
@codacy issues    # 이슈 목록
```

### Context7

```
@context7 search  # 문서 검색
```

### Brave Search

```
@brave search "query"  # 웹 검색
```

---

## 📅 정기 점검 항목

### 주간

- [ ] VS Code 에러 로그 확인
- [ ] MCP 서버 응답 시간 체크

### 월간

- [ ] 사용하지 않는 MCP 서버 정리
- [ ] 확장 프로그램 업데이트 확인
- [ ] 설정 백업

---

_최종 업데이트: 2026-01-08_
