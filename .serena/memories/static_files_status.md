# Static 파일 현황

## 문제 상황
템플릿 파일들이 다음 파일들을 참조하지만 실제로는 존재하지 않음:
- `/static/css/modern-ui.css` ❌
- `/static/js/common.js` ❌

## 현재 구조
```
static/
├── css/  (빈 폴더)
└── js/   (빈 폴더)
```

## 필요한 파일

### CSS 파일
- `static/css/modern-ui.css` - 메인 스타일시트
  - 참조 위치: `templates/base.html` (line 33)
  - 목적: 전체 프로젝트 UI 스타일
  
- `static/css/wireframe.css` - 와이어프레임 스타일 (옵션)
  - 참조 위치: `templates/ui_wireframe.html`, `templates/admin_evidence_detail.html`

### JS 파일
- `static/js/common.js` - 공통 JavaScript 모듈
  - 참조 위치: `templates/base.html` (line 77)
  - 타입: ES6 모듈 (type="module")
  - export된 함수 필요: `submitFormAsync` (upload.html에서 사용)

## 해결 방법

### 옵션 1: 최소한의 파일 생성 (권장)
빈 파일 또는 기본 스타일/스크립트로 404 에러 제거

### 옵션 2: 템플릿 수정
base.html에서 해당 참조 제거 (CDN만 사용)

### 옵션 3: 기존 파일 복구
백업이나 다른 브랜치에서 파일 복구

## CDN 사용 현황
프로젝트는 다음 CDN을 이미 사용 중:
- Bootstrap 5.1.3
- Font Awesome 6.0.0
- Google Fonts (Inter)

로컬 CSS/JS 없이도 기본 동작은 가능하나, 커스텀 스타일링 제한됨.

## 액션 필요
1. static 파일 생성 여부 결정
2. 파일 내용 정의 (있다면)
3. 또는 템플릿에서 참조 제거
