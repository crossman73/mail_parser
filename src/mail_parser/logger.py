# src/mail_parser/logger.py
import logging
import os
from datetime import datetime


def setup_logger(name='mail_parser', log_dir='logs'):
    """
    메일 파서용 로깅 시스템 설정
    """
    # 로그 디렉토리 생성
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 파일 핸들러 - 상세 로그
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"mail_parser_{timestamp}.log"
    file_handler = logging.FileHandler(
        os.path.join(log_dir, log_filename),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 콘솔 핸들러 - 기본 정보
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 포맷터 설정
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_processing_step(logger, step, message, level='info'):
    """
    처리 단계별 로깅 헬퍼 함수
    """
    formatted_message = f"[단계 {step}] {message}"

    if level.lower() == 'debug':
        logger.debug(formatted_message)
    elif level.lower() == 'warning':
        logger.warning(formatted_message)
    elif level.lower() == 'error':
        logger.error(formatted_message)
    else:
        logger.info(formatted_message)


def log_file_operation(logger, operation, filepath, success=True, error_msg=None):
    """
    파일 작업 로깅 헬퍼 함수
    """
    if success:
        logger.info(f"파일 {operation} 성공: {filepath}")
    else:
        logger.error(f"파일 {operation} 실패: {filepath} - {error_msg}")


def log_email_processing(logger, email_id, subject, status, details=None):
    """
    개별 메일 처리 로깅 헬퍼 함수
    """
    msg = f"메일 처리 - ID: {email_id[:20]}... | 제목: {subject[:50]}... | 상태: {status}"
    if details:
        msg += f" | 상세: {details}"

    if status in ['성공', 'SUCCESS']:
        logger.info(msg)
    elif status in ['제외', 'EXCLUDED']:
        logger.warning(msg)
    else:
        logger.error(msg)
