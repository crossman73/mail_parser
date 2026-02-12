"""Simple SQLite-backed evidence store.

Provides init_db(db_path), save_evidence(metadata, file_paths) and helper functions.
Now uses the unified email_parser.db via EmailDatabase singleton.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .hash_chain import build_hash_chain


def _get_db_path() -> str:
    """통합 DB 경로 반환"""
    db_path = Path('data') / 'db' / 'email_parser.db'
    return str(db_path)


def init_db(db_path: str | Path = None):
    """하위 호환성을 위해 유지. 실제로는 email_parser.db를 사용."""
    # email_parser.db의 _init_database()에서 evidence/chain_entry 테이블 생성됨
    # 이 함수는 기존 호출 코드 호환성을 위해 no-op으로 유지
    pass


def _get_conn() -> sqlite3.Connection:
    """통합 DB 연결 반환"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def save_evidence(metadata: Dict[str, Any], file_paths: List[str | Path]) -> Tuple[Optional[int], List[Dict[str, Any]]]:
    """Save evidence metadata and compute/store hash chain for provided files.

    Returns (evidence_id, chain_entries)
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO evidence (evidence_number, subject, folder_path, html_file, pdf_file, attachments_count, integrity_hash, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.get('evidence_number'),
                metadata.get('subject'),
                metadata.get('folder_path'),
                metadata.get('html_file'),
                metadata.get('pdf_file'),
                metadata.get('attachments_count', 0),
                metadata.get('integrity_hash'),
                metadata.get('generated_at')
            )
        )
        evidence_id = cur.lastrowid

        # Build and store hash chain entries
        paths = [str(p) for p in file_paths]
        chain_entries = build_hash_chain(paths)

        for entry in chain_entries:
            cur.execute(
                """
                INSERT INTO chain_entry (evidence_id, file_path, file_hash, chain_hash)
                VALUES (?, ?, ?, ?)
                """,
                (evidence_id, entry['path'],
                 entry['file_hash'], entry['chain_hash'])
            )

        # Persist final chain hash into the evidence record for quick reference.
        if chain_entries:
            final_chain = chain_entries[-1]['chain_hash']
            cur.execute('UPDATE evidence SET integrity_hash=? WHERE id=?',
                        (final_chain, evidence_id))

        conn.commit()
        return evidence_id, chain_entries
    finally:
        conn.close()


def get_evidence(evidence_id: int) -> Dict[str, Any] | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM evidence WHERE id=?', (evidence_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def list_chain_entries(evidence_id: int) -> List[Dict[str, Any]]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT file_path, file_hash, chain_hash FROM chain_entry WHERE evidence_id=? ORDER BY id', (evidence_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
