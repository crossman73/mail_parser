"""Simple SQLite-backed job store for local fallback jobs.

Now uses the unified email_parser.db instead of a separate job_store.db.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def _get_db_path() -> str:
    """통합 DB 경로 반환"""
    return str(Path('data') / 'db' / 'email_parser.db')


def init_db(path: Path = None):
    """하위 호환성을 위해 유지. 실제로는 email_parser.db를 사용."""
    # email_parser.db의 _init_database()에서 jobs 테이블 생성됨
    pass


def _get_conn():
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_job(job_id: str, status: str = 'running', result=None):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat() + 'Z'
        cur.execute('INSERT OR REPLACE INTO jobs(id, status, result, created_at, updated_at) VALUES(?,?,?,?,?)',
                    (job_id, status, json.dumps(result), now, now))
        conn.commit()
    finally:
        conn.close()


def update_job(job_id: str, status: str, result=None):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat() + 'Z'
        cur.execute('UPDATE jobs SET status=?, result=?, updated_at=? WHERE id=?',
                    (status, json.dumps(result), now, job_id))
        conn.commit()
    finally:
        conn.close()


def get_job(job_id: str):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, status, result, created_at, updated_at FROM jobs WHERE id=?', (job_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def list_jobs(limit: int = 100):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, status, result, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_job(job_id: str):
    """작업 삭제"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM jobs WHERE id=?', (job_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
