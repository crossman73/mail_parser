"""
간단한 SQLite 데이터베이스 관리자
파싱된 이메일 데이터와 파일 정보를 영구 저장합니다.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


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
                    status TEXT DEFAULT 'uploaded'
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

            conn.commit()

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
            print(f"이메일 데이터 저장 오류: {e}")
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

    def get_all_processed_files(self) -> List[Dict]:
        """모든 파싱된 파일 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pe.file_id, pe.filename, pe.process_time, pe.email_count,
                           pe.evidence_generated, uf.original_filename, uf.upload_time
                    FROM processed_emails pe
                    JOIN uploaded_files uf ON pe.file_id = uf.id
                    ORDER BY pe.process_time DESC
                """)

                rows = cursor.fetchall()
                return [{
                    'file_id': row[0],
                    'filename': row[1],
                    'process_time': row[2],
                    'email_count': row[3],
                    'evidence_generated': bool(row[4]),
                    'original_filename': row[5],
                    'upload_time': row[6]
                } for row in rows]
        except Exception as e:
            print(f"파일 목록 조회 오류: {e}")
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
            print(f"증거 생성 상태 업데이트 오류: {e}")
        return False

    def delete_processed_data(self, file_id: str) -> bool:
        """파싱된 데이터 삭제"""
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
            print(f"데이터 삭제 오류: {e}")
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
            print(f"오래된 작업 정리 오류: {e}")
        return 0


class _LazyEmailDB:
    """Lazy proxy for EmailDatabase: initialize on first attribute access.

    This preserves the existing import pattern `from src.database.email_db import db`
    but avoids creating the physical DB file at import time until a method is used.
    """

    def __init__(self, db_path: str = "email_parser.db"):
        self._db_path = db_path
        self._inst: EmailDatabase | None = None

    def _ensure(self):
        if self._inst is None:
            self._inst = EmailDatabase(self._db_path)
        return self._inst

    def __getattr__(self, name):
        inst = self._ensure()
        return getattr(inst, name)


# Lazily-initialized proxy kept for backward compatibility with imports
db = _LazyEmailDB()
