---
description: Agent 토큰 최적화 및 효율적인 프롬프트 가이드
applyTo: "**"
---

# Agent 토큰 최적화 가이드

## 🎯 핵심 원칙

1. **컨텍스트 최소화**: 필요한 파일만 참조
2. **출력 제한**: 코드만, 설명 없이
3. **단계 분리**: 한 번에 하나의 목적만

---

## 📋 프롬프트 기본 규칙

### 항상 포함할 헤더 (Claude/Copilot 공통)

```
Rules:
- Only use provided context.
- Do not analyze the entire project.
- No explanation unless asked.
- Output code only.
- Return only changed parts.
```

### 범위 고정형 지시

```
Only modify this file.
Do not read other files.
Focus on the selected code block.
```

### 출력 제한

```
Return only the changed function.
No full file output.
Diff format preferred.
```

---

## 🔄 단계 분리 전략

### ❌ 나쁜 예 (토큰 많이 소모)

```
이 프로젝트 전체를 분석하고 리팩토링하고 테스트도 작성해줘
```

### ✅ 좋은 예 (단계별 요청)

**1단계: 분석 (저비용)**

```
Summarize the current logic in 3 bullets.
No code.
```

**2단계: 제안 (중비용)**

```
Propose only the algorithm change.
No implementation.
```

**3단계: 구현 (필요한 만큼)**

```
Implement step 2 only.
Diff format.
No explanation.
```

---

## 🤖 도구별 최적 사용법

### GitHub Copilot (타이핑 보조)

- ✅ 함수 단위 자동완성
- ✅ 반복 코드 생성
- ✅ 단순 변환
- ❌ 프로젝트 분석 (비효율)
- ❌ 아키텍처 리뷰 (비효율)

### Claude Agent (분석/설계)

- ✅ 복잡한 로직 이해
- ✅ 보안/엣지 케이스 지적
- ✅ 설정 파일 검토
- ❌ 짧은 반복 코드 (Copilot이 낫다)

### MCP 도구 활용 우선순위

| 우선순위 | MCP 서버            | 용도                                |
| -------- | ------------------- | ----------------------------------- |
| 🔴 필수  | **Codacy**          | 코드 품질/보안 분석                 |
| 🔴 필수  | **Serena**          | 코드 구조 분석, 심볼 검색, 리팩토링 |
| 🟡 권장  | context7            | 문서/컨텍스트 검색                  |
| 🟡 권장  | brave-search        | 웹 검색                             |
| 🟢 선택  | memory              | 세션 메모리                         |
| 🟢 선택  | sequential-thinking | 복잡한 추론                         |

### MCP 도구 (Codacy, Serena 등)

- ✅ 코드 품질 분석
- ✅ 보안 취약점 스캔
- ✅ 특정 파일 집중 분석

---

## 📁 컨텍스트 제어

### 자동 제외 (`.agentignore` 참조)

- node_modules, .venv, **pycache**
- logs, data/db, _.log, _.db
- processed_emails, email_files
- .env, \*.lock

### 수동 제어

```
# 특정 파일만 참조
@file:src/web/admin_routes.py

# 현재 선택 영역만
@selection
```

---

## ⚠️ 절대 하지 말 것

1. "이 프로젝트 전체를 보고 개선해줘"
2. "베스트 프랙티스로 수정해줘" (범위 무한대)
3. "리팩토링해줘" (목적 불명확)
4. 한 요청에 설계+구현+테스트+설명 모두 요구

---

## ✅ 체크리스트 (요청 전 확인)

- [ ] 필요한 파일만 열었는가?
- [ ] 출력 범위를 제한했는가?
- [ ] "설명 없이"를 명시했는가?
- [ ] 한 번에 하나의 목적만 요청했는가?
- [ ] 단계를 분리했는가?

---

_최종 업데이트: 2026-01-08_
