"""
Text processing utilities.
"""

import re
from email.header import decode_header
from typing import Optional


def decode_text(header_text: Optional[str]) -> str:
    """헤더 텍스트(제목, 파일명 등)를 디코딩합니다."""
    if not header_text:
        return ""

    try:
        decoded_parts = decode_header(header_text)
        parts = []

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    # 지정된 인코딩으로 디코딩
                    if charset:
                        parts.append(part.decode(charset, errors='ignore'))
                    else:
                        # 인코딩이 지정되지 않은 경우 순서대로 시도
                        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin1']:
                            try:
                                parts.append(part.decode(encoding))
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # 모든 인코딩이 실패한 경우
                            parts.append(part.decode(
                                'utf-8', errors='replace'))
                except (UnicodeDecodeError, LookupError):
                    # fallback으로 cp949 사용 (한국어 이메일 대응)
                    try:
                        parts.append(part.decode('cp949', errors='ignore'))
                    except:
                        parts.append(part.decode('utf-8', errors='replace'))
            else:
                parts.append(str(part))

        return ''.join(parts)

    except Exception as e:
        print(f"텍스트 디코딩 오류: {e}")
        return str(header_text)


def sanitize_filename(filename: str) -> str:
    """파일명을 안전하게 정리합니다."""
    if not filename:
        return "unnamed"

    # 공백을 언더스코어로 변경
    sanitized = filename.replace(" ", "_")

    # Windows/Unix에서 사용할 수 없는 문자 제거
    invalid_chars = r'[\\/*?:"<>|]'
    sanitized = re.sub(invalid_chars, "", sanitized)

    # 연속된 언더스코어 정리
    sanitized = re.sub(r'__+', '_', sanitized)

    # 앞뒤 공백과 점 제거
    sanitized = sanitized.strip('._')

    # 길이 제한 (Windows 파일명 길이 제한 고려)
    max_length = 150
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit(
            '.', 1) if '.' in sanitized else (sanitized, '')
        if ext:
            name = name[:max_length - len(ext) - 1]
            sanitized = f"{name}.{ext}"
        else:
            sanitized = sanitized[:max_length]

    # 빈 문자열 처리
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def clean_email_content(content: str) -> str:
    """이메일 내용을 정리합니다."""
    if not content:
        return ""

    # HTML 태그 제거 (간단한 버전)
    content = re.sub(r'<[^>]+>', '', content)

    # 연속된 공백 정리
    content = re.sub(r'\s+', ' ', content)

    # 앞뒤 공백 제거
    content = content.strip()

    return content


def extract_email_addresses(text: str) -> list:
    """텍스트에서 이메일 주소를 추출합니다."""
    if not text:
        return []

    # 이메일 주소 패턴
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    return re.findall(email_pattern, text)


def normalize_subject(subject: str) -> str:
    """제목을 정규화합니다."""
    if not subject:
        return "(제목없음)"

    # Re:, Fwd: 등의 접두사 제거
    subject = re.sub(r'^(Re|RE|Fwd|FWD|답장|전달):\s*',
                     '', subject, flags=re.IGNORECASE)

    # 연속된 공백 정리
    subject = re.sub(r'\s+', ' ', subject)

    # 앞뒤 공백 제거
    subject = subject.strip()

    return subject or "(제목없음)"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자릅니다."""
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
