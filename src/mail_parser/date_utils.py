"""
Date processing utilities.
"""

import email.utils
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import re


def get_email_date(message) -> datetime:
    """이메일 메시지에서 날짜를 파싱하여 datetime 객체로 반환합니다."""
    date_str = message.get('Date')
    if not date_str:
        return datetime.now()

    try:
        # email.utils.parsedate_to_datetime 사용
        return email.utils.parsedate_to_datetime(date_str)
    except (TypeError, ValueError, OverflowError):
        pass

    # fallback 처리
    try:
        # 수동 파싱 시도
        return parse_date_fallback(date_str)
    except:
        return datetime.now()


def parse_date_fallback(date_str: str) -> datetime:
    """날짜 문자열을 수동으로 파싱합니다."""
    if not date_str:
        return datetime.now()

    # 일반적인 이메일 날짜 형식들
    date_formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    # 시간대 정보 정리
    date_str = re.sub(r'\s*\([^)]+\)', '', date_str)  # (KST) 같은 부분 제거
    date_str = re.sub(r'\s+', ' ', date_str).strip()

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # 모든 형식이 실패하면 현재 시간 반환
    return datetime.now()


def format_korean_date(dt: datetime) -> str:
    """날짜를 한국어 형식으로 포맷합니다."""
    return dt.strftime("%Y년 %m월 %d일 %H시 %M분")


def format_court_date(dt: datetime) -> str:
    """법정 제출용 날짜 형식으로 포맷합니다."""
    return dt.strftime("%Y. %m. %d.")


def format_filename_date(dt: datetime) -> str:
    """파일명용 날짜 형식으로 포맷합니다."""
    return dt.strftime("%Y-%m-%d")


def format_iso_date(dt: datetime) -> str:
    """ISO 형식으로 날짜를 포맷합니다."""
    return dt.isoformat()


def parse_korean_date(date_str: str) -> Optional[datetime]:
    """한국어 날짜 문자열을 파싱합니다."""
    if not date_str:
        return None

    korean_formats = [
        "%Y년 %m월 %d일 %H시 %M분",
        "%Y년 %m월 %d일",
        "%Y. %m. %d. %H:%M",
        "%Y. %m. %d.",
    ]

    for fmt in korean_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def get_date_range_description(start_date: datetime, end_date: datetime) -> str:
    """날짜 범위를 설명하는 문자열을 생성합니다."""
    if start_date.date() == end_date.date():
        return f"{format_korean_date(start_date)}"

    duration = (end_date - start_date).days

    if duration == 1:
        return f"{format_korean_date(start_date)} ~ {format_korean_date(end_date)} (1일)"
    else:
        return f"{format_korean_date(start_date)} ~ {format_korean_date(end_date)} ({duration}일)"


def is_business_day(dt: datetime) -> bool:
    """평일인지 확인합니다."""
    return dt.weekday() < 5  # 월요일(0) ~ 금요일(4)


def get_business_days_count(start_date: datetime, end_date: datetime) -> int:
    """기간 내 평일 수를 계산합니다."""
    count = 0
    current = start_date.date()
    end = end_date.date()

    while current <= end:
        if current.weekday() < 5:  # 월-금
            count += 1
        current = current + timedelta(days=1)

    return count


def normalize_timezone(dt: datetime, target_tz: Optional[timezone] = None) -> datetime:
    """시간대를 정규화합니다."""
    if target_tz is None:
        target_tz = timezone.utc

    if dt.tzinfo is None:
        # naive datetime은 로컬 시간으로 가정
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(target_tz)


def get_relative_time_description(dt: datetime, reference: Optional[datetime] = None) -> str:
    """상대적 시간 설명을 반환합니다."""
    if reference is None:
        reference = datetime.now()

    if dt.tzinfo != reference.tzinfo:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=reference.tzinfo)
        elif reference.tzinfo is None:
            reference = reference.replace(tzinfo=dt.tzinfo)
        else:
            dt = dt.astimezone(reference.tzinfo)

    delta = reference - dt

    if delta.days > 0:
        return f"{delta.days}일 전"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours}시간 전"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes}분 전"
    else:
        return "방금 전"
