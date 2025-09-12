import email
import re
from datetime import datetime
from email.header import decode_header


def decode_text(header_text):
    """Decode an email header into a unicode string."""
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
    """Sanitize a filename for safe filesystem use."""
    if not filename:
        return ""
    sanitized = filename.replace(' ', '_')
    sanitized = re.sub(r'[\\/*?:"<>|]', '', sanitized).strip()
    sanitized = re.sub(r'__+', '_', sanitized)
    return sanitized[:150]


def get_email_date(msg):
    """Return a datetime extracted from a message's Date header or now()."""
    date_str = None
    try:
        date_str = msg.get('Date')
    except Exception:
        return datetime.now()

    if not date_str:
        return datetime.now()

    try:
        return email.utils.parsedate_to_datetime(date_str)
    except Exception:
        return datetime.now()
