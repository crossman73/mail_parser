"""Simple SQLite-backed job store for local fallback jobs.

This is intentionally minimal: used for development convenience so that
local fallback jobs survive a process restart. Not intended as a
production-grade queue.
"""
from pathlib import Path
import sqlite3
import json
from datetime import datetime

DB_PATH = Path('data') / 'job_store.db'

_SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT,
    result TEXT,
    created_at TEXT,
    updated_at TEXT
);
'''


def init_db(path: Path = None):
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(_SCHEMA)
    conn.commit()
    return conn


def _get_conn():
    return init_db()


def create_job(job_id: str, status: str = 'running', result=None):
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + 'Z'
    cur.execute('INSERT OR REPLACE INTO jobs(id, status, result, created_at, updated_at) VALUES(?,?,?,?,?)',
                (job_id, status, json.dumps(result), now, now))
    conn.commit()


def update_job(job_id: str, status: str, result=None):
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + 'Z'
    cur.execute('UPDATE jobs SET status=?, result=?, updated_at=? WHERE id=?',
                (status, json.dumps(result), now, job_id))
    conn.commit()


def get_job(job_id: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, status, result, created_at, updated_at FROM jobs WHERE id=?', (job_id,))
    row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def list_jobs(limit: int = 100):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, status, result, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]
