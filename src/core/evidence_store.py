"""Simple SQLite-backed evidence store.

Provides init_db(db_path), save_evidence(metadata, file_paths) and helper functions.
This is intentionally lightweight to integrate quickly with the existing pipeline.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .hash_chain import build_hash_chain

_DB_CONN: sqlite3.Connection | None = None


def init_db(db_path: str | Path):
    global _DB_CONN
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # evidence table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_number TEXT,
        subject TEXT,
        folder_path TEXT,
        html_file TEXT,
        pdf_file TEXT,
        attachments_count INTEGER,
        integrity_hash TEXT,
        generated_at TEXT
    )
    """)

    # chain entries
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chain_entry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id INTEGER,
        file_path TEXT,
        file_hash TEXT,
        chain_hash TEXT,
        FOREIGN KEY(evidence_id) REFERENCES evidence(id)
    )
    """)

    conn.commit()
    _DB_CONN = conn


def _get_conn() -> sqlite3.Connection:
    if _DB_CONN is None:
        raise RuntimeError(
            "evidence DB not initialized. Call init_db(db_path) first.")
    return _DB_CONN


def save_evidence(metadata: Dict[str, Any], file_paths: List[str | Path]) -> Tuple[Optional[int], List[Dict[str, Any]]]:
    """Save evidence metadata and compute/store hash chain for provided files.

    Returns (evidence_id, chain_entries)
    """
    conn = _get_conn()
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


def get_evidence(evidence_id: int) -> Dict[str, Any] | None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM evidence WHERE id=?', (evidence_id,))
    row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def list_chain_entries(evidence_id: int) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT file_path, file_hash, chain_hash FROM chain_entry WHERE evidence_id=? ORDER BY id', (evidence_id,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]
