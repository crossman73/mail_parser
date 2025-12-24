"""
설정 관리자 - DB 기반 설정 저장소 (폴백 지원)
DB 연결 실패 시 메모리 기반 폴백 사용
"""
import logging
import os
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    DB 기반 설정 관리자

    특징:
    - DB에 설정 영구 저장
    - DB 실패 시 메모리 폴백 (웹 서비스 계속 동작)
    - 환경변수 우선순위 지원
    - 스레드 안전
    """

    def __init__(self):
        self._lock = Lock()
        self._memory_fallback: Dict[str, Any] = {}
        self._db_available = False
        self._db = None
        self._init_db()

    def _init_db(self):
        """DB 초기화 (실패해도 계속 진행)"""
        try:
            from src.database.email_db import db
            self._db = db
            # DB 연결 테스트
            _ = self._db.get_setting('_test_connection', default='ok')
            self._db_available = True
            logger.info("✅ 설정 DB 연결 성공")
        except Exception as e:
            self._db_available = False
            logger.warning(f"⚠️ 설정 DB 연결 실패 (메모리 폴백 사용): {e}")

    def get(self, key: str, default: Any = None, use_env: bool = True) -> Any:
        """
        설정 값 조회

        우선순위:
        1. 환경변수 (use_env=True인 경우)
        2. DB
        3. 메모리 폴백
        4. default
        """
        # 1. 환경변수 확인
        if use_env:
            env_key = key.upper().replace('.', '_').replace('-', '_')
            env_value = os.getenv(env_key)
            if env_value is not None:
                return self._convert_env_value(env_value)

        # 2. DB 확인
        if self._db_available:
            try:
                value = self._db.get_setting(key, default=None)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning(f"DB 설정 조회 오류 ({key}): {e}")
                # DB 실패 시 메모리 폴백으로 전환
                self._db_available = False

        # 3. 메모리 폴백
        with self._lock:
            if key in self._memory_fallback:
                return self._memory_fallback[key]

        # 4. 기본값
        return default

    def set(self, key: str, value: Any, description: Optional[str] = None,
            category: str = 'general', is_sensitive: bool = False,
            changed_by: str = 'system', reason: Optional[str] = None) -> bool:
        """설정 값 저장 (DB + 메모리 폴백)"""
        success = False

        # DB 저장 시도
        if self._db_available:
            try:
                success = self._db.set_setting(
                    key, value, description, category,
                    is_sensitive, changed_by, reason
                )
            except Exception as e:
                logger.warning(f"DB 설정 저장 오류 ({key}): {e}")
                self._db_available = False

        # 메모리 폴백에도 저장
        with self._lock:
            self._memory_fallback[key] = value

        if not self._db_available:
            logger.info(f"⚠️ 설정이 메모리에만 저장됨 (DB 불가): {key}")

        return success or True  # 메모리라도 저장되면 성공

    def delete(self, key: str, changed_by: str = 'system',
               reason: Optional[str] = None) -> bool:
        """설정 삭제"""
        success = False

        # DB 삭제 시도
        if self._db_available:
            try:
                success = self._db.delete_setting(key, changed_by, reason)
            except Exception as e:
                logger.warning(f"DB 설정 삭제 오류 ({key}): {e}")

        # 메모리에서도 삭제
        with self._lock:
            self._memory_fallback.pop(key, None)

        return success

    def get_all(self, category: Optional[str] = None,
                include_sensitive: bool = False) -> Dict[str, Any]:
        """모든 설정 조회"""
        if self._db_available:
            try:
                return self._db.get_all_settings(category, include_sensitive)
            except Exception as e:
                logger.warning(f"DB 전체 설정 조회 오류: {e}")

        # 메모리 폴백 반환
        with self._lock:
            if category:
                # 카테고리 필터링은 DB에서만 가능
                return {}
            return dict(self._memory_fallback)

    def get_metadata(self, category: Optional[str] = None):
        """설정 메타데이터 조회 (관리 UI용)"""
        if self._db_available:
            try:
                return self._db.get_settings_metadata(category)
            except Exception as e:
                logger.warning(f"설정 메타데이터 조회 오류: {e}")
        return []

    def get_history(self, key: Optional[str] = None, limit: int = 50):
        """설정 변경 이력 조회"""
        if self._db_available:
            try:
                return self._db.get_settings_history(key, limit)
            except Exception as e:
                logger.warning(f"설정 이력 조회 오류: {e}")
        return []

    def is_db_available(self) -> bool:
        """DB 사용 가능 여부"""
        return self._db_available

    def retry_db_connection(self) -> bool:
        """DB 재연결 시도"""
        self._init_db()
        return self._db_available

    def _convert_env_value(self, value: str) -> Any:
        """환경변수 값을 적절한 타입으로 변환"""
        # bool 변환
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        if value.lower() in ('false', '0', 'no', 'off'):
            return False

        # int 변환 시도
        try:
            return int(value)
        except ValueError:
            pass

        # float 변환 시도
        try:
            return float(value)
        except ValueError:
            pass

        # 문자열 반환
        return value

    # 편의 메서드
    def get_bool(self, key: str, default: bool = False) -> bool:
        """bool 설정 조회"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """int 설정 조회"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_str(self, key: str, default: str = '') -> str:
        """string 설정 조회"""
        value = self.get(key, default)
        return str(value) if value is not None else default


# 전역 싱글톤 인스턴스
_settings_manager: Optional[SettingsManager] = None
_init_lock = Lock()


def get_settings_manager() -> SettingsManager:
    """설정 관리자 싱글톤 인스턴스 반환"""
    global _settings_manager
    if _settings_manager is None:
        with _init_lock:
            if _settings_manager is None:
                _settings_manager = SettingsManager()
    return _settings_manager
