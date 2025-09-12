"""Unified DB manager wrappers for evidence, job_store, and email database.

Use this module to initialize DBs and call CRUD operations from other code
without coupling import-time side-effects.

Example:
    from src.core import db_manager
    db_manager.init_all()
    eid, entries = db_manager.save_evidence(metadata, file_paths)
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def init_all(evidence_path: Optional[Path] = None, job_store_path: Optional[Path] = None):
    """Initialize all known DBs (safe to call multiple times)."""
    evidence_path = Path(evidence_path) if evidence_path else Path(
        'data') / 'evidence.db'
    job_store_path = Path(job_store_path) if job_store_path else Path(
        'data') / 'job_store.db'

    # Evidence DB (lazy init)
    try:
        from src.core import evidence_store
        evidence_store.init_db(evidence_path)
    except Exception:
        # Don't fail hard; callers can handle missing DB
        pass

    # Job store
    try:
        from src.core import job_store
        job_store.init_db(job_store_path)
    except Exception:
        pass


# Evidence helpers -----------------------------------------------------------
def save_evidence(metadata: Dict[str, Any], file_paths: List[str | Path]) -> Tuple[int, List[Dict[str, Any]]]:
    from src.core import evidence_store

    # Ensure DB initialized if not already
    try:
        evidence_store._get_conn()
    except Exception:
        evidence_store.init_db(Path('data') / 'evidence.db')
    return evidence_store.save_evidence(metadata, file_paths)


def get_evidence(evidence_id: int) -> Optional[Dict[str, Any]]:
    from src.core import evidence_store
    try:
        return evidence_store.get_evidence(evidence_id)
    except Exception:
        return None


def list_evidence(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List evidence rows (simple wrapper)."""
    from src.core import evidence_store
    conn = None
    try:
        conn = evidence_store._get_conn()
    except Exception:
        evidence_store.init_db(Path('data') / 'evidence.db')
    conn = evidence_store._get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, evidence_number, subject, generated_at, integrity_hash FROM evidence ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def delete_evidence(evidence_id: int) -> bool:
    from src.core import evidence_store
    try:
        conn = evidence_store._get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM chain_entry WHERE evidence_id=?',
                    (evidence_id,))
        cur.execute('DELETE FROM evidence WHERE id=?', (evidence_id,))
        conn.commit()
        return True
    except Exception:
        return False


# Job store helpers ----------------------------------------------------------
def create_job(job_id: str, status: str = 'running', result: Any = None):
    from src.core import job_store
    try:
        job_store._get_conn()
    except Exception:
        job_store.init_db()
    job_store.create_job(job_id, status=status, result=result)


def update_job(job_id: str, status: str, result: Any = None):
    from src.core import job_store
    try:
        job_store._get_conn()
    except Exception:
        job_store.init_db()
    job_store.update_job(job_id, status=status, result=result)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    from src.core import job_store
    try:
        return job_store.get_job(job_id)
    except Exception:
        return None


def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    from src.core import job_store
    try:
        return job_store.list_jobs(limit)
    except Exception:
        try:
            job_store.init_db()
            return job_store.list_jobs(limit)
        except Exception:
            return []


# Email DB helpers (uses src.database.email_db.db which is lazy now)
def get_processed_files() -> List[Dict[str, Any]]:
    try:
        from src.database.email_db import db as email_db
        return email_db.get_all_processed_files()
    except Exception:
        return []


# Logging helpers ------------------------------------------------------------
def write_log(level: str, message: str, extra: Any = None) -> int:
    try:
        from src.core import log_store
        try:
            log_store._get_conn()
        except Exception:
            log_store.init_db()
        return log_store.write_log(level, message, str(extra) if extra is not None else None)
    except Exception:
        return -1


def list_logs(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        from src.core import log_store
        return log_store.list_logs(limit)
    except Exception:
        return []


# Simple key/value settings stored in a small SQLite DB (data/settings.db)
def set_setting(key: str, value: str) -> bool:
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path('data') / 'settings.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        cur.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_setting(key: str) -> str | None:
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path('data') / 'settings.db'
        if not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return row[0]
    except Exception:
        return None
