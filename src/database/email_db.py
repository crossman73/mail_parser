"""
간단한 SQLite 데이터베이스 관리자
파싱된 이메일 데이터와 파일 정보를 영구 저장합니다.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 로거 설정
logger = logging.getLogger('mail_parser')


class EmailDatabase:
    def __init__(self, db_path: str = "email_parser.db"):
        """데이터베이스 초기화"""
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """데이터베이스 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 업로드된 파일 정보 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_size INTEGER,
                    upload_time TEXT NOT NULL,
                    file_path TEXT,
                    status TEXT DEFAULT 'uploaded',
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    deleted_reason TEXT
                )
            """)

            # 파싱된 이메일 데이터 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_emails (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    process_time TEXT NOT NULL,
                    email_count INTEGER,
                    emails_data TEXT,  -- JSON 형태로 저장
                    evidence_generated INTEGER DEFAULT 0,
                    generated_evidence TEXT,  -- JSON 형태로 저장
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files (id)
                )
            """)

            # 진행 상황 추적 테이블 (선택적)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_tasks (
                    id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)

            # 시스템 로그 테이블 (웹 UI 조회용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_no INTEGER,
                    thread_id INTEGER,
                    process_id INTEGER,
                    extra_data TEXT
                )
            """)

            # 로그 조회 성능을 위한 인덱스
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp
                ON system_logs(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_level
                ON system_logs(level)
            """)

            # 시스템 설정 테이블 (key-value 저장소)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'string',
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    is_sensitive INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT DEFAULT 'system'
                )
            """)

            # 설정 변경 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TEXT NOT NULL,
                    changed_by TEXT DEFAULT 'system',
                    reason TEXT
                )
            """)

            # 시스템 테스트 정의 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_key TEXT UNIQUE NOT NULL,
                    test_name TEXT NOT NULL,
                    test_category TEXT NOT NULL,
                    test_description TEXT,
                    test_module TEXT NOT NULL,
                    test_function TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    timeout_seconds INTEGER DEFAULT 30,
                    display_order INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 테스트 실행 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER NOT NULL,
                    execution_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_message TEXT,
                    error_detail TEXT,
                    duration_ms INTEGER,
                    executed_by TEXT DEFAULT 'system',
                    FOREIGN KEY (test_id) REFERENCES system_tests (id)
                )
            """)

            conn.commit()

    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)

    def save_uploaded_file(self, file_id: str, filename: str, original_filename: str,
                           file_size: int, file_path: Optional[str] = None) -> bool:
        """업로드된 파일 정보 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO uploaded_files
                    (id, filename, original_filename, file_size, upload_time, file_path, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'uploaded')
                """, (file_id, filename, original_filename, file_size,
                      datetime.now().isoformat(), file_path))
                conn.commit()
                return True
        except Exception as e:
            print(f"파일 정보 저장 오류: {e}")
            return False

    def save_processed_emails(self, file_id: str, filename: str, emails_data: List[Dict]) -> bool:
        """파싱된 이메일 데이터 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO processed_emails
                    (id, file_id, filename, process_time, email_count, emails_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (file_id, file_id, filename, datetime.now().isoformat(),
                      len(emails_data), json.dumps(emails_data, ensure_ascii=False, default=str)))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"이메일 데이터 저장 오류: {e}", exc_info=True)
            return False

    def get_processed_emails(self, file_id: str) -> Optional[Dict]:
        """파싱된 이메일 데이터 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pe.*, uf.original_filename, uf.file_size, uf.upload_time
                    FROM processed_emails pe
                    JOIN uploaded_files uf ON pe.file_id = uf.id
                    WHERE pe.file_id = ?
                """, (file_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'file_id': row[1],
                        'filename': row[2],
                        'process_time': row[3],
                        'email_count': row[4],
                        'emails': json.loads(row[5]) if row[5] else [],
                        'evidence_generated': bool(row[6]),
                        'generated_evidence': json.loads(row[7]) if row[7] else [],
                        'original_filename': row[8],
                        'file_size': row[9],
                        'upload_time': row[10]
                    }
        except Exception as e:
            print(f"이메일 데이터 조회 오류: {e}")
        return None

    def get_all_processed_files(self, include_deleted: bool = False) -> List[Dict]:
        """
        모든 파싱된 파일 목록 조회

        Args:
            include_deleted: 삭제된 파일 포함 여부 (기본 False)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if include_deleted:
                    query = """
                        SELECT pe.file_id, pe.filename, pe.process_time, pe.email_count,
                               pe.evidence_generated, uf.original_filename, uf.upload_time,
                               pe.deleted, pe.deleted_at
                        FROM processed_emails pe
                        JOIN uploaded_files uf ON pe.file_id = uf.id
                        ORDER BY pe.process_time DESC
                    """
                else:
                    query = """
                        SELECT pe.file_id, pe.filename, pe.process_time, pe.email_count,
                               pe.evidence_generated, uf.original_filename, uf.upload_time,
                               pe.deleted, pe.deleted_at
                        FROM processed_emails pe
                        JOIN uploaded_files uf ON pe.file_id = uf.id
                        WHERE pe.deleted = 0
                        ORDER BY pe.process_time DESC
                    """

                cursor.execute(query)
                rows = cursor.fetchall()
                return [{
                    'file_id': row[0],
                    'filename': row[1],
                    'process_time': row[2],
                    'email_count': row[3],
                    'evidence_generated': bool(row[4]),
                    'original_filename': row[5],
                    'upload_time': row[6],
                    'deleted': bool(row[7]),
                    'deleted_at': row[8]
                } for row in rows]
        except Exception as e:
            logger.error(f"파일 목록 조회 오류: {e}", exc_info=True)
            return []

    def update_evidence_generated(self, file_id: str, evidence_data: List[str]) -> bool:
        """증거 생성 완료 상태 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE processed_emails
                    SET evidence_generated = 1, generated_evidence = ?
                    WHERE file_id = ?
                """, (json.dumps(evidence_data, ensure_ascii=False), file_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"증거 생성 상태 업데이트 오류: {e}", exc_info=True)
            return False

    def get_all_uploaded_files(self, include_deleted: bool = False) -> List[Dict]:
        """
        모든 업로드된 파일 목록 조회

        Args:
            include_deleted: 삭제된 파일 포함 여부 (기본 False)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if include_deleted:
                    query = """
                        SELECT uf.id, uf.filename, uf.original_filename, uf.file_size,
                               uf.upload_time, uf.file_path, uf.status,
                               uf.deleted, uf.deleted_at, uf.deleted_reason,
                               COUNT(pe.id) as processed_count
                        FROM uploaded_files uf
                        LEFT JOIN processed_emails pe ON uf.id = pe.file_id AND pe.deleted = 0
                        GROUP BY uf.id
                        ORDER BY uf.upload_time DESC
                    """
                else:
                    query = """
                        SELECT uf.id, uf.filename, uf.original_filename, uf.file_size,
                               uf.upload_time, uf.file_path, uf.status,
                               uf.deleted, uf.deleted_at, uf.deleted_reason,
                               COUNT(pe.id) as processed_count
                        FROM uploaded_files uf
                        LEFT JOIN processed_emails pe ON uf.id = pe.file_id AND pe.deleted = 0
                        WHERE uf.deleted = 0
                        GROUP BY uf.id
                        ORDER BY uf.upload_time DESC
                    """

                cursor.execute(query)
                rows = cursor.fetchall()
                return [{
                    'file_id': row[0],
                    'filename': row[1],
                    'original_filename': row[2],
                    'file_size': row[3],
                    'upload_time': row[4],
                    'file_path': row[5],
                    'status': row[6],
                    'deleted': bool(row[7]),
                    'deleted_at': row[8],
                    'deleted_reason': row[9],
                    'processed_count': row[10]
                } for row in rows]
        except Exception as e:
            logger.error(f"업로드 파일 목록 조회 오류: {e}", exc_info=True)
            return []

    def soft_delete_file(self, file_id: str, reason: str = None) -> bool:
        """
        파일 소프트 삭제 (DB 레코드 유지, 상태만 변경)

        Args:
            file_id: 삭제할 파일 ID
            reason: 삭제 사유 (선택)

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                # uploaded_files 테이블 소프트 삭제
                cursor.execute("""
                    UPDATE uploaded_files
                    SET deleted = 1, deleted_at = ?, deleted_reason = ?, status = 'deleted'
                    WHERE id = ?
                """, (now, reason, file_id))

                # 관련 processed_emails도 소프트 삭제
                cursor.execute("""
                    UPDATE processed_emails
                    SET deleted = 1, deleted_at = ?
                    WHERE file_id = ?
                """, (now, file_id))

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"소프트 삭제 오류: {e}", exc_info=True)
            return False

    def delete_processed_data(self, file_id: str) -> bool:
        """파싱된 데이터 완전 삭제 (하드 삭제)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM processed_emails WHERE file_id = ?", (file_id,))
                cursor.execute(
                    "DELETE FROM uploaded_files WHERE id = ?", (file_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"데이터 삭제 오류: {e}", exc_info=True)
            return False

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """오래된 작업 데이터 정리"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM processing_tasks
                    WHERE updated_at < ? AND status IN ('completed', 'error')
                """, (cutoff_iso,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"오래된 작업 정리 오류: {e}", exc_info=True)
            return 0

    def save_log(self, timestamp: str, level: str, logger_name: str, message: str,
                 module: Optional[str] = None, function: Optional[str] = None,
                 line_no: Optional[int] = None, thread_id: Optional[int] = None,
                 process_id: Optional[int] = None, extra_data: Optional[Dict] = None) -> bool:
        """시스템 로그 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_logs
                    (timestamp, level, logger_name, message, module, function,
                     line_no, thread_id, process_id, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, level, logger_name, message, module, function,
                    line_no, thread_id, process_id,
                    json.dumps(
                        extra_data, ensure_ascii=False) if extra_data else None
                ))
                conn.commit()
                return True
        except Exception as e:
            # 로그 저장 실패 시 콘솔 출력 (순환 방지)
            print(f"[DB] 로그 저장 오류: {e}")
            return False

    def get_logs(self, limit: int = 1000, offset: int = 0,
                 level: Optional[str] = None,
                 start_time: Optional[str] = None,
                 end_time: Optional[str] = None) -> List[Dict]:
        """시스템 로그 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM system_logs WHERE 1=1"
                params = []

                if level:
                    query += " AND level = ?"
                    params.append(level)
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                logs = []
                for row in rows:
                    log_dict = dict(row)
                    if log_dict.get('extra_data'):
                        try:
                            log_dict['extra_data'] = json.loads(
                                log_dict['extra_data'])
                        except Exception:
                            pass
                    logs.append(log_dict)

                return logs
        except Exception as e:
            print(f"[DB] 로그 조회 오류: {e}")
            return []

    def get_log_count(self, level: Optional[str] = None,
                      start_time: Optional[str] = None,
                      end_time: Optional[str] = None) -> int:
        """로그 개수 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT COUNT(*) FROM system_logs WHERE 1=1"
                params = []

                if level:
                    query += " AND level = ?"
                    params.append(level)
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)

                cursor.execute(query, params)
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"[DB] 로그 카운트 오류: {e}")
            return 0

    def clear_logs(self, before_time: Optional[str] = None) -> int:
        """로그 삭제 (전체 또는 특정 시간 이전)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if before_time:
                    cursor.execute(
                        "DELETE FROM system_logs WHERE timestamp < ?", (before_time,))
                else:
                    cursor.execute("DELETE FROM system_logs")
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        except Exception as e:
            print(f"[DB] 로그 삭제 오류: {e}")
            return 0

    # ========================================================================
    # 설정 관리 메서드
    # ========================================================================

    def get_setting(self, key: str, default: Any = None) -> Any:
        """설정 값 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value, type FROM system_settings WHERE key = ?", (key,))
                row = cursor.fetchone()

                if row is None:
                    return default

                value = row['value']
                value_type = row['type']

                # 타입에 따라 변환
                if value_type == 'int':
                    return int(value)
                elif value_type == 'float':
                    return float(value)
                elif value_type == 'bool':
                    return value.lower() in ('true', '1', 'yes', 'on')
                elif value_type == 'json':
                    return json.loads(value)
                else:  # string
                    return value

        except Exception as e:
            print(f"[DB] 설정 조회 오류 ({key}): {e}")
            return default

    def set_setting(self, key: str, value: Any, description: Optional[str] = None,
                    category: str = 'general', is_sensitive: bool = False,
                    changed_by: str = 'system', reason: Optional[str] = None) -> bool:
        """설정 값 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 기존 값 조회 (히스토리용 및 created_at 유지)
                cursor.execute(
                    "SELECT value, created_at FROM system_settings WHERE key = ?", (key,))
                old_row = cursor.fetchone()
                old_value = old_row[0] if old_row else None
                created_at = old_row[1] if old_row else datetime.now().isoformat()

                # 타입 결정
                if isinstance(value, bool):
                    value_type = 'bool'
                    value_str = str(value)
                elif isinstance(value, int):
                    value_type = 'int'
                    value_str = str(value)
                elif isinstance(value, float):
                    value_type = 'float'
                    value_str = str(value)
                elif isinstance(value, (dict, list)):
                    value_type = 'json'
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_type = 'string'
                    value_str = str(value)

                # 설정 저장 (created_at 유지, updated_at 갱신)
                cursor.execute("""
                    INSERT OR REPLACE INTO system_settings
                    (key, value, type, description, category, is_sensitive, created_at, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (key, value_str, value_type, description, category,
                      1 if is_sensitive else 0, created_at, datetime.now().isoformat(), changed_by))

                # 히스토리 저장
                if old_value != value_str:
                    cursor.execute("""
                        INSERT INTO settings_history
                        (setting_key, old_value, new_value, changed_at, changed_by, reason)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (key, old_value, value_str, datetime.now().isoformat(),
                          changed_by, reason))

                conn.commit()
                return True

        except Exception as e:
            print(f"[DB] 설정 저장 오류 ({key}): {e}")
            return False

    def delete_setting(self, key: str, changed_by: str = 'system',
                       reason: Optional[str] = None) -> bool:
        """설정 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 기존 값 조회
                cursor.execute(
                    "SELECT value FROM system_settings WHERE key = ?", (key,))
                old_row = cursor.fetchone()
                old_value = old_row[0] if old_row else None

                if old_value:
                    # 히스토리 저장
                    cursor.execute("""
                        INSERT INTO settings_history
                        (setting_key, old_value, new_value, changed_at, changed_by, reason)
                        VALUES (?, ?, NULL, ?, ?, ?)
                    """, (key, old_value, datetime.now().isoformat(), changed_by, reason))

                # 설정 삭제
                cursor.execute(
                    "DELETE FROM system_settings WHERE key = ?", (key,))
                conn.commit()
                return True

        except Exception as e:
            print(f"[DB] 설정 삭제 오류 ({key}): {e}")
            return False

    def get_all_settings(self, category: Optional[str] = None,
                         include_sensitive: bool = False) -> Dict[str, Any]:
        """모든 설정 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM system_settings WHERE 1=1"
                params = []

                if category:
                    query += " AND category = ?"
                    params.append(category)

                if not include_sensitive:
                    query += " AND is_sensitive = 0"

                query += " ORDER BY category, key"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                settings = {}
                for row in rows:
                    key = row['key']
                    value = row['value']
                    value_type = row['type']

                    # 타입 변환
                    if value_type == 'int':
                        settings[key] = int(value)
                    elif value_type == 'float':
                        settings[key] = float(value)
                    elif value_type == 'bool':
                        settings[key] = value.lower() in (
                            'true', '1', 'yes', 'on')
                    elif value_type == 'json':
                        settings[key] = json.loads(value)
                    else:
                        settings[key] = value

                return settings

        except Exception as e:
            print(f"[DB] 전체 설정 조회 오류: {e}")
            return {}

    def get_settings_metadata(self, category: Optional[str] = None) -> List[Dict]:
        """설정 메타데이터 조회 (관리 UI용)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM system_settings WHERE 1=1"
                params = []

                if category:
                    query += " AND category = ?"
                    params.append(category)

                query += " ORDER BY category, key"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                metadata = []
                for row in rows:
                    item = dict(row)
                    # 민감한 값은 마스킹
                    if item.get('is_sensitive'):
                        item['value'] = '********'
                    metadata.append(item)

                return metadata

        except Exception as e:
            print(f"[DB] 설정 메타데이터 조회 오류: {e}")
            return []

    def get_settings_history(self, key: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """설정 변경 이력 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if key:
                    query = """
                        SELECT * FROM settings_history
                        WHERE setting_key = ?
                        ORDER BY changed_at DESC LIMIT ?
                    """
                    cursor.execute(query, (key, limit))
                else:
                    query = """
                        SELECT * FROM settings_history
                        ORDER BY changed_at DESC LIMIT ?
                    """
                    cursor.execute(query, (limit,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            print(f"[DB] 설정 이력 조회 오류: {e}")
            return []


class _LazyEmailDB:
    """Lazy proxy for EmailDatabase: initialize on first attribute access.

    This preserves the existing import pattern `from src.database.email_db import db`
    but avoids creating the physical DB file at import time until a method is used.
    """

    def __init__(self, db_path: str = "data/db/email_parser.db"):
        self._db_path = db_path
        self._inst: EmailDatabase | None = None

    def _ensure(self):
        if self._inst is None:
            # 데이터베이스 디렉토리 생성
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._inst = EmailDatabase(self._db_path)
        return self._inst

    def __getattr__(self, name):
        inst = self._ensure()
        return getattr(inst, name)


class SystemTestManager:
    """시스템 테스트 관리"""

    def __init__(self, db_path: str = "data/db/email_parser.db"):
        self.db_path = db_path

    def add_test(self, test_key: str, test_name: str, test_category: str,
                 test_module: str, test_function: str, test_description: str = "",
                 is_enabled: bool = True, timeout_seconds: int = 30,
                 display_order: int = 0) -> bool:
        """테스트 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT OR REPLACE INTO system_tests
                    (test_key, test_name, test_category, test_description, test_module,
                     test_function, is_enabled, timeout_seconds, display_order, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (test_key, test_name, test_category, test_description, test_module,
                      test_function, 1 if is_enabled else 0, timeout_seconds, display_order, now, now))

                conn.commit()
                return True
        except Exception as e:
            print(f"테스트 추가 오류: {e}")
            return False

    def get_all_tests(self, category: Optional[str] = None, enabled_only: bool = False) -> List[Dict]:
        """모든 테스트 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM system_tests WHERE 1=1"
                params = []

                if category:
                    query += " AND test_category = ?"
                    params.append(category)

                if enabled_only:
                    query += " AND is_enabled = 1"

                query += " ORDER BY display_order, test_name"

                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"테스트 조회 오류: {e}")
            return []

    def get_test_by_key(self, test_key: str) -> Optional[Dict]:
        """특정 테스트 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM system_tests WHERE test_key = ?", (test_key,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"테스트 조회 오류: {e}")
            return None

    def update_test(self, test_key: str, **kwargs) -> bool:
        """테스트 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 허용된 필드만 업데이트
                allowed_fields = ['test_name', 'test_category', 'test_description',
                                'test_module', 'test_function', 'is_enabled',
                                'timeout_seconds', 'display_order']

                updates = []
                params = []

                for field, value in kwargs.items():
                    if field in allowed_fields:
                        updates.append(f"{field} = ?")
                        params.append(value)

                if not updates:
                    return False

                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(test_key)

                query = f"UPDATE system_tests SET {', '.join(updates)} WHERE test_key = ?"
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            print(f"테스트 업데이트 오류: {e}")
            return False

    def delete_test(self, test_key: str) -> bool:
        """테스트 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM system_tests WHERE test_key = ?", (test_key,))
                conn.commit()
                return True
        except Exception as e:
            print(f"테스트 삭제 오류: {e}")
            return False

    def save_execution(self, test_id: int, status: str, result_message: str = "",
                      error_detail: str = "", duration_ms: int = 0,
                      executed_by: str = "system") -> bool:
        """테스트 실행 결과 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO test_executions
                    (test_id, execution_time, status, result_message, error_detail,
                     duration_ms, executed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (test_id, datetime.now().isoformat(), status, result_message,
                      error_detail, duration_ms, executed_by))

                conn.commit()
                return True
        except Exception as e:
            print(f"실행 결과 저장 오류: {e}")
            return False

    def get_execution_history(self, test_key: str = None, limit: int = 50) -> List[Dict]:
        """실행 이력 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if test_key:
                    query = """
                        SELECT e.*, t.test_key, t.test_name, t.test_category
                        FROM test_executions e
                        JOIN system_tests t ON e.test_id = t.id
                        WHERE t.test_key = ?
                        ORDER BY e.execution_time DESC
                        LIMIT ?
                    """
                    cursor.execute(query, (test_key, limit))
                else:
                    query = """
                        SELECT e.*, t.test_key, t.test_name, t.test_category
                        FROM test_executions e
                        JOIN system_tests t ON e.test_id = t.id
                        ORDER BY e.execution_time DESC
                        LIMIT ?
                    """
                    cursor.execute(query, (limit,))

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"실행 이력 조회 오류: {e}")
            return []

    def get_test_categories(self) -> List[str]:
        """테스트 카테고리 목록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT test_category FROM system_tests ORDER BY test_category")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"카테고리 조회 오류: {e}")
            return []


# Lazily-initialized proxy kept for backward compatibility with imports
db = _LazyEmailDB()
test_manager = SystemTestManager()

