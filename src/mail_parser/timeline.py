"""
TimelineBuilder — EmailModel 리스트에서 타임라인을 구축하고 DB에 저장/로드.

data/db/email_parser.db의 timelines, timeline_events 테이블 사용.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.models.timeline_model import (
    TimelineModel,
    TimelineEvent,
    TimelineEventType,
)

DB_PATH = str(Path('data') / 'db' / 'email_parser.db')


def _get_conn(db_path: str = None) -> sqlite3.Connection:
    """DB 연결 반환"""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


class TimelineBuilder:
    """이메일/증거에서 타임라인을 구축하고 DB에 저장하는 빌더"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH

    # ─── 타임라인 생성 ───────────────────────────────────

    def build_from_emails(
        self,
        emails: list,
        title: str = None,
        source_file: str = None,
    ) -> TimelineModel:
        """EmailModel 리스트 → TimelineModel 생성

        Args:
            emails: EmailModel 인스턴스 리스트 (또는 dict 리스트)
            title: 타임라인 제목
            source_file: 원본 파일명

        Returns:
            TimelineModel (DB 미저장 상태)
        """
        now = datetime.now().isoformat()
        timeline = TimelineModel(
            title=title or f"이메일 타임라인 ({len(emails)}건)",
            source_file=source_file,
            status='draft',
            created_at=now,
            updated_at=now,
        )

        for idx, email in enumerate(emails):
            event = self._email_to_event(email, idx)
            if event:
                timeline.add_event(event)

        timeline.update_date_range()
        return timeline

    def _email_to_event(self, email, sort_order: int = 0) -> Optional[TimelineEvent]:
        """EmailModel(또는 dict) → TimelineEvent 변환"""
        try:
            # EmailModel dataclass 또는 dict 처리
            if hasattr(email, 'date'):
                ts = email.date if isinstance(email.date, datetime) else datetime.now()
                title = getattr(email, 'subject', '제목없음')
                sender = getattr(email, 'sender', '')
                recipients = getattr(email, 'recipients', [])
                attachments = getattr(email, 'attachments', [])
                msg_id = getattr(email, 'message_id', '')
                in_reply_to = getattr(email, 'in_reply_to', None)
            elif isinstance(email, dict):
                date_str = email.get('date', '')
                ts = self._parse_date(date_str) if date_str else datetime.now()
                title = email.get('subject', email.get('title', '제목없음'))
                sender = email.get('sender', email.get('from', ''))
                recipients = email.get('recipients', [])
                if isinstance(recipients, str):
                    recipients = [recipients]
                attachments = email.get('attachments', [])
                msg_id = email.get('message_id', '')
                in_reply_to = email.get('in_reply_to')
            else:
                return None

            # 이벤트 타입 결정
            if in_reply_to:
                event_type = TimelineEventType.EMAIL_REPLIED
            else:
                event_type = TimelineEventType.EMAIL_SENT

            participants = [sender] + recipients if sender else recipients

            return TimelineEvent(
                timestamp=ts,
                title=title,
                event_type=event_type,
                description=f"발신: {sender}" if sender else None,
                email_id=msg_id,
                source_file=getattr(email, 'output_directory', None) and str(email.output_directory),
                participants=participants,
                attachments=attachments,
                sort_order=sort_order,
                is_key_event=len(attachments) > 0,
            )
        except Exception:
            return None

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """다양한 날짜 형식 파싱"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%Y/%m/%d',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return datetime.now()

    # ─── DB 저장 ────────────────────────────────────────

    def save_timeline(self, timeline: TimelineModel) -> int:
        """타임라인과 이벤트를 DB에 저장 (hash chain 자동 계산)

        Returns:
            생성된 timeline id
        """
        # 이벤트 해시 계산
        for event in timeline.events:
            event.hash_value = event.compute_hash()

        # 타임라인 해시 계산 (이벤트 해시 기반)
        timeline.hash = timeline.compute_hash()

        conn = _get_conn(self.db_path)
        try:
            cursor = conn.cursor()

            # 타임라인 INSERT
            tl_data = timeline.to_db_dict()
            cursor.execute("""
                INSERT INTO timelines
                    (title, description, date_range_start, date_range_end,
                     source_file, created_at, updated_at, status, hash)
                VALUES
                    (:title, :description, :date_range_start, :date_range_end,
                     :source_file, :created_at, :updated_at, :status, :hash)
            """, tl_data)

            timeline_id = cursor.lastrowid
            timeline.id = timeline_id

            # 이벤트 INSERT
            for event in timeline.events:
                event.timeline_id = timeline_id
                ev_data = event.to_db_dict()
                cursor.execute("""
                    INSERT INTO timeline_events
                        (timeline_id, event_type, timestamp, title, description,
                         email_id, evidence_id, source_file, attachments_json,
                         participants_json, sort_order, is_key_event,
                         legal_significance, notes, hash_value, verified,
                         created_at, updated_at)
                    VALUES
                        (:timeline_id, :event_type, :timestamp, :title, :description,
                         :email_id, :evidence_id, :source_file, :attachments_json,
                         :participants_json, :sort_order, :is_key_event,
                         :legal_significance, :notes, :hash_value, :verified,
                         :created_at, :updated_at)
                """, ev_data)
                event.id = cursor.lastrowid

            conn.commit()
            return timeline_id
        finally:
            conn.close()

    def update_timeline(self, timeline: TimelineModel) -> bool:
        """기존 타임라인 메타데이터 업데이트"""
        if not timeline.id:
            return False
        conn = _get_conn(self.db_path)
        try:
            tl_data = timeline.to_db_dict()
            tl_data['id'] = timeline.id
            conn.execute("""
                UPDATE timelines
                SET title=:title, description=:description,
                    date_range_start=:date_range_start, date_range_end=:date_range_end,
                    source_file=:source_file, updated_at=:updated_at,
                    status=:status, hash=:hash
                WHERE id=:id
            """, tl_data)
            conn.commit()
            return True
        finally:
            conn.close()

    # ─── DB 조회 ────────────────────────────────────────

    def load_timeline(self, timeline_id: int) -> Optional[TimelineModel]:
        """DB에서 타임라인 + 이벤트 로드"""
        conn = _get_conn(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM timelines WHERE id=?", (timeline_id,)
            ).fetchone()
            if not row:
                return None

            event_rows = conn.execute(
                "SELECT * FROM timeline_events WHERE timeline_id=? ORDER BY sort_order, timestamp",
                (timeline_id,)
            ).fetchall()

            events = [TimelineEvent.from_db_row(dict(r)) for r in event_rows]
            timeline = TimelineModel.from_db_row(dict(row), events=events)

            # participants / event_types 동기화
            for e in events:
                timeline.participants.update(e.participants)
                if isinstance(e.event_type, TimelineEventType):
                    timeline.event_types.add(e.event_type)

            return timeline
        finally:
            conn.close()

    def list_timelines(self, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """타임라인 목록 조회 (이벤트 미포함, 메타만)"""
        conn = _get_conn(self.db_path)
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM timelines WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM timelines ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()

            result = []
            for row in rows:
                d = dict(row)
                # 이벤트 수 집계
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM timeline_events WHERE timeline_id=?",
                    (d['id'],)
                ).fetchone()[0]
                d['event_count'] = cnt
                result.append(d)
            return result
        finally:
            conn.close()

    def delete_timeline(self, timeline_id: int) -> bool:
        """타임라인 + 연관 이벤트 삭제"""
        conn = _get_conn(self.db_path)
        try:
            conn.execute("DELETE FROM timeline_events WHERE timeline_id=?", (timeline_id,))
            cursor = conn.execute("DELETE FROM timelines WHERE id=?", (timeline_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ─── 이벤트 CRUD ───────────────────────────────────

    def add_event(self, timeline_id: int, event: TimelineEvent) -> int:
        """타임라인에 이벤트 추가 (hash 자동 계산 + 타임라인 해시 갱신)"""
        event.timeline_id = timeline_id
        event.hash_value = event.compute_hash()

        conn = _get_conn(self.db_path)
        try:
            ev_data = event.to_db_dict()
            cursor = conn.execute("""
                INSERT INTO timeline_events
                    (timeline_id, event_type, timestamp, title, description,
                     email_id, evidence_id, source_file, attachments_json,
                     participants_json, sort_order, is_key_event,
                     legal_significance, notes, hash_value, verified,
                     created_at, updated_at)
                VALUES
                    (:timeline_id, :event_type, :timestamp, :title, :description,
                     :email_id, :evidence_id, :source_file, :attachments_json,
                     :participants_json, :sort_order, :is_key_event,
                     :legal_significance, :notes, :hash_value, :verified,
                     :created_at, :updated_at)
            """, ev_data)
            conn.commit()

            event.id = cursor.lastrowid

            # 타임라인 해시 갱신
            self._refresh_timeline_hash(conn, timeline_id)
            conn.commit()

            return event.id
        finally:
            conn.close()

    def update_event(self, event: TimelineEvent) -> bool:
        """이벤트 수정 (hash 재계산 + 타임라인 해시 갱신)"""
        if not event.id:
            return False
        event.hash_value = event.compute_hash()
        conn = _get_conn(self.db_path)
        try:
            ev_data = event.to_db_dict()
            ev_data['id'] = event.id
            conn.execute("""
                UPDATE timeline_events
                SET event_type=:event_type, timestamp=:timestamp, title=:title,
                    description=:description, email_id=:email_id,
                    evidence_id=:evidence_id, source_file=:source_file,
                    attachments_json=:attachments_json,
                    participants_json=:participants_json,
                    sort_order=:sort_order, is_key_event=:is_key_event,
                    legal_significance=:legal_significance, notes=:notes,
                    hash_value=:hash_value, verified=:verified,
                    updated_at=:updated_at
                WHERE id=:id
            """, ev_data)
            conn.commit()

            # 타임라인 해시 갱신
            if event.timeline_id:
                self._refresh_timeline_hash(conn, event.timeline_id)
                conn.commit()

            return True
        finally:
            conn.close()

    def _refresh_timeline_hash(self, conn, timeline_id: int):
        """이벤트 해시들로부터 타임라인 해시 재계산 후 DB 갱신"""
        rows = conn.execute(
            "SELECT hash_value FROM timeline_events WHERE timeline_id=? ORDER BY sort_order, id",
            (timeline_id,)
        ).fetchall()
        event_hashes = [r['hash_value'] or '' for r in rows]

        row = conn.execute("SELECT title FROM timelines WHERE id=?", (timeline_id,)).fetchone()
        title = row['title'] if row else ''

        data = f"{title}|{'|'.join(event_hashes)}"
        import hashlib
        new_hash = hashlib.sha256(data.encode()).hexdigest()[:32]

        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE timelines SET hash=?, updated_at=? WHERE id=?",
            (new_hash, now, timeline_id)
        )

    def delete_event(self, event_id: int, timeline_id: int = None) -> bool:
        """이벤트 삭제 (타임라인 해시 갱신)"""
        conn = _get_conn(self.db_path)
        try:
            # timeline_id 미제공 시 조회
            if not timeline_id:
                row = conn.execute(
                    "SELECT timeline_id FROM timeline_events WHERE id=?", (event_id,)
                ).fetchone()
                if row:
                    timeline_id = row['timeline_id']

            cursor = conn.execute(
                "DELETE FROM timeline_events WHERE id=?", (event_id,)
            )
            conn.commit()

            if cursor.rowcount > 0 and timeline_id:
                self._refresh_timeline_hash(conn, timeline_id)
                conn.commit()

            return cursor.rowcount > 0
        finally:
            conn.close()

    def reorder_events(self, timeline_id: int, event_ids: List[int]) -> bool:
        """이벤트 순서 재정렬

        Args:
            timeline_id: 타임라인 ID
            event_ids: 새 순서의 이벤트 ID 리스트
        """
        conn = _get_conn(self.db_path)
        try:
            for idx, eid in enumerate(event_ids):
                conn.execute(
                    "UPDATE timeline_events SET sort_order=?, updated_at=? WHERE id=? AND timeline_id=?",
                    (idx, datetime.now().isoformat(), eid, timeline_id)
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_event(self, event_id: int) -> Optional[TimelineEvent]:
        """단일 이벤트 조회"""
        conn = _get_conn(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM timeline_events WHERE id=?", (event_id,)
            ).fetchone()
            if not row:
                return None
            return TimelineEvent.from_db_row(dict(row))
        finally:
            conn.close()
