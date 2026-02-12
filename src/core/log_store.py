"""Log store - now delegates to system_logs in email_parser.db.

The separate logs.db is no longer used. All logging goes to system_logs
table in the unified email_parser.db.
"""
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_db_path() -> str:
    """통합 DB 경로 반환"""
    return str(Path('data') / 'db' / 'email_parser.db')


def init_db(path: Path | None = None):
    """하위 호환성을 위해 유지. 실제로는 email_parser.db를 사용."""
    pass


def _get_conn():
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def write_log(level: str, message: str, extra: Any = None) -> Optional[int]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        now = datetime.now(UTC).isoformat()
        extra_text = None
        try:
            if extra is not None:
                extra_text = json.dumps(extra, ensure_ascii=False, default=str)
        except Exception:
            extra_text = str(extra)
        cur.execute(
            'INSERT INTO system_logs(timestamp, level, logger_name, message, extra_data) VALUES(?,?,?,?,?)',
            (now, level, 'log_store', message, extra_text))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, level, message, extra_data as extra, timestamp as created_at FROM system_logs ORDER BY id DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
