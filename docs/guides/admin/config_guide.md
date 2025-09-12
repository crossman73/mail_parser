# 설정 파일 가이드

## config.json 설정 옵션

### 기본 필터링 옵션

#### 1. exclude_keywords (제외할 키워드)
메일 제목이나 내용에 다음 키워드가 포함된 메일을 자동으로 제외합니다.

```json
"exclude_keywords": [
  "광고", "프로모션", "뉴스레터", "newsletter",
  "unsubscribe", "구독해지", "마케팅", "marketing"
]
```

#### 2. exclude_senders (제외할 발신자)
특정 패턴의 발신자 주소를 가진 메일을 제외합니다.

```json
"exclude_senders": [
  "noreply@", "no-reply@", "marketing@", "newsletter@"
]
```

#### 3. exclude_domains (제외할 도메인)
특정 도메인에서 온 메일을 모두 제외합니다.

```json
"exclude_domains": [
  "mailchimp.com", "constantcontact.com", "sendinblue.com"
]
```

#### 4. date_range (날짜 범위)
사건과 관련된 기간 외의 메일을 제외합니다.

```json
"date_range": {
  "start": "2020-01-01",  # 이 날짜 이전 메일 제외
  "end": "2025-12-31"     # 이 날짜 이후 메일 제외
}
```

#### 5. required_keywords (필수 키워드)
이 키워드들 중 하나라도 포함된 메일만 처리합니다. (빈 배열이면 모든 메일 허용)

```json
"required_keywords": {
  "keywords": ["계약", "합의", "송금", "지급"]
}
```

### 처리 옵션

#### processing_options
```json
"processing_options": {
  "max_subject_length": 100,           # 제목 최대 길이 (폴더명용)
  "preserve_thread_structure": true,   # 메일 스레드 구조 보존
  "generate_hash_verification": true,  # SHA-256 해시값 생성
  "create_backup": true                # 원본 백업 생성
}
```

#### output_settings
```json
"output_settings": {
  "evidence_number_format": "{party} 제{number}호증",  # 증거번호 형식
  "folder_name_format": "[{date}]_{subject}",         # 폴더명 형식
  "pdf_title_position": "center_top",                 # PDF 제목 위치
  "include_metadata": true                            # 메타데이터 포함 여부
}
```

## 사용 시나리오별 설정 예시

### 1. 계약 관련 소송용
```json
{
  "exclude_keywords": ["광고", "프로모션", "마케팅"],
  "required_keywords": {
    "keywords": ["계약", "합의서", "약정", "체결"]
  },
  "date_range": {
    "start": "2023-01-01",
    "end": "2023-12-31"
  }
}
```

### 2. 금전 관련 분쟁용
```json
{
  "exclude_keywords": ["광고", "뉴스레터"],
  "required_keywords": {
    "keywords": ["송금", "입금", "지급", "대금", "청구서", "영수증"]
  },
  "exclude_domains": ["bank-ad.co.kr", "promotion.co.kr"]
}
```

### 3. 모든 메일 보존 (필터링 최소화)
```json
{
  "exclude_keywords": [],
  "exclude_senders": ["noreply@", "system@"],
  "required_keywords": {
    "keywords": []
  },
  "date_range": {
    "start": "1900-01-01",
    "end": "2099-12-31"
  }
}
```

## 설정 파일 적용 방법

### 기본 설정 파일 사용
```powershell
python main.py email_files/example.mbox --party 갑
```

### 사용자 정의 설정 파일 사용
```powershell
python main.py email_files/example.mbox --party 갑 --config custom_config.json
```

### 설정 파일 검증
설정 파일의 JSON 문법이 올바른지 확인하려면:

```powershell
python -m json.tool config.json
```

## 주의사항

1. **JSON 문법**: 설정 파일은 올바른 JSON 형식이어야 합니다.
2. **인코딩**: UTF-8 인코딩으로 저장해야 합니다.
3. **날짜 형식**: YYYY-MM-DD 형식을 사용합니다.
4. **키워드 대소문자**: 대소문자를 구분하지 않습니다.
5. **백업**: 중요한 설정 변경 전에는 항상 백업을 만드세요.
