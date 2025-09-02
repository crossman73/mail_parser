# src/mail_parser/utils.py
import re
from email.header import decode_header
from datetime import datetime
import email

def decode_text(header_text):
    """헤더 텍스트(제목, 파일명 등)를 디코딩합니다."""
    if not header_text:
        return ""
    decoded_parts = decode_header(header_text)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(charset or 'utf-8', errors='ignore'))
            except (UnicodeDecodeError, LookupError):
                parts.append(part.decode('cp949', errors='ignore'))
        else:
            parts.append(str(part))
    return ''.join(parts)

def sanitize_filename(filename):
    """공백을 '_'로 바꾸고, 파일 및 폴더명으로 사용할 수 없는 문자를 제거합니다."""
    sanitized = filename.replace(" ", "_")
    sanitized = re.sub(r'[\\/*?:"<>|]', "", sanitized).strip()
    sanitized = re.sub(r'__+', '_', sanitized)
    return sanitized[:150]

def get_email_date(msg):
    """이메일 메시지에서 날짜를 파싱하여 datetime 객체로 반환합니다."""
    date_str = msg.get('Date')
    if not date_str:
        return datetime.now()
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        return datetime.now()
