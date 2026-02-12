"""Unified DB manager wrappers for evidence, job_store, and email database.

All data now stored in the single email_parser.db.
Use this module to call CRUD operations from other code
without coupling import-time side-effects.

Example:
    from ..core import db_manager
    db_manager.init_all()
    eid, entries = db_manager.save_evidence(metadata, file_paths)
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def init_all(evidence_path: Optional[Path] = None, job_store_path: Optional[Path] = None):
    """Initialize all known DBs (safe to call multiple times).
    Now delegates to email_parser.db singleton — individual store init_db() are no-ops.
    """
    # Evidence DB (now uses email_parser.db)
    try:
        from ..core import evidence_store
        evidence_store.init_db()
    except Exception as e:
        print(f"⚠️ Evidence store 초기화 실패: {e}")

    # Job store (now uses email_parser.db)
    try:
        from ..core import job_store
        job_store.init_db()
    except Exception as e:
        print(f"⚠️ Job store 초기화 실패: {e}")


# Evidence helpers -----------------------------------------------------------
def save_evidence(metadata: Dict[str, Any], file_paths: List[str | Path]) -> Tuple[int, List[Dict[str, Any]]]:
    from ..core import evidence_store
    return evidence_store.save_evidence(metadata, file_paths)


def get_evidence(evidence_id: int) -> Optional[Dict[str, Any]]:
    from ..core import evidence_store
    try:
        return evidence_store.get_evidence(evidence_id)
    except Exception:
        return None


def list_evidence(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List evidence rows (simple wrapper)."""
    from ..core import evidence_store
    conn = evidence_store._get_conn()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, evidence_number, subject, generated_at, integrity_hash FROM evidence ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_evidence(evidence_id: int) -> bool:
    from ..core import evidence_store
    try:
        conn = evidence_store._get_conn()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM chain_entry WHERE evidence_id=?',
                        (evidence_id,))
            cur.execute('DELETE FROM evidence WHERE id=?', (evidence_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


# Job store helpers ----------------------------------------------------------
def create_job(job_id: str, status: str = 'running', result: Any = None):
    from ..core import job_store
    job_store.create_job(job_id, status=status, result=result)


def update_job(job_id: str, status: str, result: Any = None):
    from ..core import job_store
    job_store.update_job(job_id, status=status, result=result)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    from ..core import job_store
    try:
        return job_store.get_job(job_id)
    except Exception:
        return None


def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    from ..core import job_store
    try:
        return job_store.list_jobs(limit)
    except Exception:
        return []


# Email DB helpers (uses src.database.email_db.db which is lazy now)
def get_processed_files() -> List[Dict[str, Any]]:
    try:
        from ..database.email_db import db as email_db
        return email_db.get_all_processed_files()
    except Exception:
        return []


# Logging helpers ------------------------------------------------------------
def write_log(level: str, message: str, extra: Any = None) -> int:
    try:
        from ..core import log_store
        return log_store.write_log(level, message, str(extra) if extra is not None else None)
    except Exception:
        return -1


def list_logs(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        from ..core import log_store
        return log_store.list_logs(limit)
    except Exception:
        return []


# Settings helpers — use email_parser.db system_settings table
def set_setting(key: str, value: str) -> bool:
    try:
        from ..database.email_db import db as email_db
        email_db.set_setting(key, value)
        return True
    except Exception:
        return False


def get_setting(key: str) -> str | None:
    try:
        from ..database.email_db import db as email_db
        return email_db.get_setting(key)
    except Exception:
        return None
