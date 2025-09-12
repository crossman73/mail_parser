import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path('data') / 'logs.db'


def init_db(path: Path | None = None):
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,
        message TEXT,
        extra TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    return conn


def _get_conn():
    return init_db()


def write_log(level: str, message: str, extra: Any = None) -> Optional[int]:
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + 'Z'
    extra_text = None
    try:
        if extra is not None:
            extra_text = json.dumps(extra, ensure_ascii=False, default=str)
    except Exception:
        extra_text = str(extra)
    cur.execute('INSERT INTO logs(level, message, extra, created_at) VALUES(?,?,?,?)',
                (level, message, extra_text, now))
    conn.commit()
    return cur.lastrowid


def list_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, level, message, extra, created_at FROM logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]
