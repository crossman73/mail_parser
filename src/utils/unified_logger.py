"""
통합 로깅 시스템 - 웹 뷰어와 파일 로깅
"""
import logging
import os
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class WebLogHandler(logging.Handler):
    """웹에서 실시간으로 볼 수 있는 로그 핸들러"""

    def __init__(self, maxlen=1000):
        super().__init__()
        self.logs = deque(maxlen=maxlen)  # 최대 1000개 로그 유지
        self.lock = threading.Lock()

    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno
            }
            with self.lock:
                self.logs.append(log_entry)
        except Exception:
            self.handleError(record)

    def get_logs(self, level: str = None, limit: int = 100) -> List[Dict]:
        """최근 로그 가져오기"""
        with self.lock:
            logs = list(self.logs)

        if level:
            logs = [log for log in logs if log['level'] == level.upper()]

        return logs[-limit:]

    def clear_logs(self):
        """로그 초기화"""
        with self.lock:
            self.logs.clear()


# 전역 웹 로그 핸들러
_web_log_handler = None


def get_web_log_handler() -> WebLogHandler:
    """전역 웹 로그 핸들러 가져오기"""
    global _web_log_handler
    if _web_log_handler is None:
        _web_log_handler = WebLogHandler()
    return _web_log_handler


def setup_unified_logger(name='mail_parser', log_dir='logs', enable_web=True):
    """
    통합 로깅 시스템 설정 (파일 + 콘솔 + 웹)

    Args:
        name: 로거 이름
        log_dir: 로그 파일 디렉토리
        enable_web: 웹 로그 핸들러 활성화 여부
    """
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 1. 파일 핸들러 - 상세 로그
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"mail_parser_{timestamp}.log"
    file_handler = logging.FileHandler(
        log_path / log_filename,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 2. 콘솔 핸들러 - 기본 정보
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 3. 웹 로그 핸들러 - 실시간 웹 뷰어용
    if enable_web:
        web_handler = get_web_log_handler()
        web_handler.setLevel(logging.DEBUG)

    # 포맷터 설정
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    if enable_web:
        web_handler.setFormatter(detailed_formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    if enable_web:
        logger.addHandler(web_handler)

    logger.info(f"✅ 통합 로깅 시스템 초기화 완료 (파일: {log_filename}, 웹: {enable_web})")

    return logger


def setup_flask_logger(app, enable_web=True):
    """
    Flask 애플리케이션 로거 설정

    Args:
        app: Flask 애플리케이션
        enable_web: 웹 로그 핸들러 활성화 여부
    """
    # Flask 기본 로거 레벨 설정
    app.logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # 로그 디렉토리
    log_path = Path('logs')
    log_path.mkdir(exist_ok=True)

    # 1. 파일 핸들러
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"flask_app_{timestamp}.log"
    file_handler = logging.FileHandler(
        log_path / log_filename,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 2. 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 3. 웹 로그 핸들러
    if enable_web:
        web_handler = get_web_log_handler()
        web_handler.setLevel(logging.DEBUG)

    # 포맷터
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(detailed_formatter)
    if enable_web:
        web_handler.setFormatter(detailed_formatter)

    # 핸들러 추가
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    if enable_web:
        app.logger.addHandler(web_handler)

    app.logger.info(f"✅ Flask 로거 초기화 완료 (웹 뷰어: {enable_web})")


def get_recent_logs(level: str = None, limit: int = 100) -> List[Dict]:
    """
    최근 로그 가져오기

    Args:
        level: 로그 레벨 필터 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        limit: 가져올 로그 수

    Returns:
        로그 리스트
    """
    handler = get_web_log_handler()
    return handler.get_logs(level, limit)


def get_log_files(log_dir='logs', limit=10) -> List[Dict]:
    """
    로그 파일 목록 가져오기

    Args:
        log_dir: 로그 디렉토리
        limit: 가져올 파일 수

    Returns:
        로그 파일 정보 리스트
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return []

    log_files = []
    for log_file in sorted(log_path.glob('*.log'), key=os.path.getmtime, reverse=True)[:limit]:
        stat = log_file.stat()
        log_files.append({
            'name': log_file.name,
            'path': str(log_file),
            'size': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return log_files


def read_log_file(filename: str, log_dir='logs', lines: int = 500) -> List[str]:
    """
    로그 파일 읽기

    Args:
        filename: 로그 파일명
        log_dir: 로그 디렉토리
        lines: 읽을 줄 수 (마지막 N줄)

    Returns:
        로그 라인 리스트
    """
    log_path = Path(log_dir) / filename
    if not log_path.exists():
        return []

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"로그 파일 읽기 실패: {str(e)}"]
