"""
Timeline data model for email visualization.
DB 테이블(timelines, timeline_events)과 호환되는 데이터 모델.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum


class TimelineEventType(Enum):
    """타임라인 이벤트 유형"""
    EMAIL = "email"
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    EMAIL_REPLIED = "email_replied"
    ATTACHMENT_ADDED = "attachment_added"
    EVIDENCE_CREATED = "evidence_created"
    ADDITIONAL_EVIDENCE = "additional_evidence"
    DOCUMENT = "document"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"


@dataclass
class TimelineEvent:
    """타임라인 이벤트 (DB timeline_events 테이블 호환)"""

    # 필수 필드
    timestamp: datetime = None
    title: str = ""

    # DB 기본 키
    id: Optional[int] = None
    timeline_id: Optional[int] = None
    event_type: TimelineEventType = TimelineEventType.EMAIL
    description: Optional[str] = None

    # 관련 엔티티
    email_id: Optional[str] = None
    evidence_id: Optional[int] = None
    source_file: Optional[str] = None

    # 리스트 필드 (DB에서는 JSON 직렬화)
    participants: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 이벤트 속성
    sort_order: int = 0
    is_key_event: bool = False
    legal_significance: Optional[str] = None
    notes: Optional[str] = None
    hash_value: Optional[str] = None
    verified: bool = False

    # 타임스탬프
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 레거시 호환 (기존 TimelineGenerator 용)
    event_id: Optional[str] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def compute_hash(self) -> str:
        """이벤트 해시 계산"""
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        data = f"{ts}|{self.title}|{self.email_id or ''}|{self.evidence_id or ''}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_db_dict(self) -> Dict[str, Any]:
        """DB INSERT/UPDATE용 딕셔너리"""
        now = datetime.now().isoformat()
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        et = self.event_type.value if isinstance(self.event_type, TimelineEventType) else self.event_type
        return {
            'timeline_id': self.timeline_id,
            'event_type': et,
            'timestamp': ts,
            'title': self.title,
            'description': self.description,
            'email_id': self.email_id,
            'evidence_id': self.evidence_id,
            'source_file': self.source_file,
            'attachments_json': json.dumps(self.attachments, ensure_ascii=False) if self.attachments else None,
            'participants_json': json.dumps(self.participants, ensure_ascii=False) if self.participants else None,
            'sort_order': self.sort_order,
            'is_key_event': 1 if self.is_key_event else 0,
            'legal_significance': self.legal_significance,
            'notes': self.notes,
            'hash_value': self.hash_value or self.compute_hash(),
            'verified': 1 if self.verified else 0,
            'created_at': self.created_at or now,
            'updated_at': now,
        }

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'TimelineEvent':
        """DB 행에서 생성"""
        timestamp = row.get('timestamp', '')
        if isinstance(timestamp, str) and timestamp:
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.now()
        elif not timestamp:
            timestamp = datetime.now()

        event_type_str = row.get('event_type', 'email')
        try:
            event_type = TimelineEventType(event_type_str)
        except ValueError:
            event_type = TimelineEventType.EMAIL

        attachments = []
        if row.get('attachments_json'):
            try:
                attachments = json.loads(row['attachments_json'])
            except (json.JSONDecodeError, TypeError):
                pass

        participants = []
        if row.get('participants_json'):
            try:
                participants = json.loads(row['participants_json'])
            except (json.JSONDecodeError, TypeError):
                pass

        return cls(
            id=row.get('id'),
            timeline_id=row.get('timeline_id'),
            event_type=event_type,
            timestamp=timestamp,
            title=row.get('title', ''),
            description=row.get('description'),
            email_id=row.get('email_id'),
            evidence_id=row.get('evidence_id'),
            source_file=row.get('source_file'),
            attachments=attachments,
            participants=participants,
            sort_order=row.get('sort_order', 0),
            is_key_event=bool(row.get('is_key_event', 0)),
            legal_significance=row.get('legal_significance'),
            notes=row.get('notes'),
            hash_value=row.get('hash_value'),
            verified=bool(row.get('verified', 0)),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """API 응답용 딕셔너리"""
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        et = self.event_type.value if isinstance(self.event_type, TimelineEventType) else self.event_type
        return {
            'id': self.id,
            'event_id': self.event_id or (f"event_{self.id}" if self.id else None),
            'timeline_id': self.timeline_id,
            'event_type': et,
            'timestamp': ts,
            'title': self.title,
            'description': self.description,
            'email_id': self.email_id,
            'evidence_id': self.evidence_id,
            'source_file': self.source_file,
            'participants': self.participants,
            'attachments': self.attachments,
            'sort_order': self.sort_order,
            'is_key_event': self.is_key_event,
            'legal_significance': self.legal_significance,
            'notes': self.notes,
            'hash_value': self.hash_value,
            'verified': self.verified,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class TimelineModel:
    """타임라인 데이터 모델 (DB timelines 테이블 호환)"""

    # 필수 필드
    title: str = ""

    # DB 기본 키
    id: Optional[int] = None
    description: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    source_file: Optional[str] = None
    status: str = 'draft'
    hash: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # In-memory 이벤트 목록
    events: List[TimelineEvent] = field(default_factory=list)

    # 레거시 호환
    timeline_id: Optional[str] = None
    created_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    participants: Set[str] = field(default_factory=set)
    event_types: Set[TimelineEventType] = field(default_factory=set)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """초기화 후 처리"""
        if self.created_date and not self.created_at:
            self.created_at = self.created_date.isoformat()

    @property
    def event_count(self) -> int:
        """이벤트 개수"""
        return len(self.events)

    @property
    def duration(self) -> Optional[int]:
        """타임라인 기간 (일)"""
        if not self.events:
            return None
        timestamps = [e.timestamp for e in self.events if isinstance(e.timestamp, datetime)]
        if not timestamps:
            return None
        return (max(timestamps) - min(timestamps)).days

    @property
    def participant_count(self) -> int:
        """참여자 수"""
        all_participants = set()
        for event in self.events:
            all_participants.update(event.participants)
        return len(all_participants)

    def add_event(self, event: TimelineEvent) -> None:
        """이벤트 추가"""
        self.events.append(event)
        self.events.sort(key=lambda x: x.timestamp if isinstance(x.timestamp, datetime) else datetime.min)
        self.participants.update(event.participants)
        if isinstance(event.event_type, TimelineEventType):
            self.event_types.add(event.event_type)

    def remove_event(self, event_id) -> bool:
        """이벤트 제거 (id 또는 event_id로)"""
        original_count = len(self.events)
        self.events = [
            e for e in self.events
            if e.id != event_id and e.event_id != str(event_id)
        ]
        return len(self.events) < original_count

    def get_event(self, event_id) -> Optional[TimelineEvent]:
        """이벤트 조회 (id 또는 event_id로)"""
        for event in self.events:
            if event.id == event_id or event.event_id == str(event_id):
                return event
        return None

    def get_events_by_date(self, target_date: datetime) -> List[TimelineEvent]:
        """특정 날짜의 이벤트 조회"""
        target_str = target_date.strftime("%Y-%m-%d")
        return [
            event for event in self.events
            if isinstance(event.timestamp, datetime)
            and event.timestamp.strftime("%Y-%m-%d") == target_str
        ]

    def get_events_by_type(self, event_type: TimelineEventType) -> List[TimelineEvent]:
        """특정 유형의 이벤트 조회"""
        return [event for event in self.events if event.event_type == event_type]

    def get_events_by_participant(self, participant: str) -> List[TimelineEvent]:
        """특정 참여자의 이벤트 조회"""
        return [
            event for event in self.events
            if participant in event.participants
        ]

    def filter_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[TimelineEventType]] = None,
        participants: Optional[List[str]] = None
    ) -> List[TimelineEvent]:
        """이벤트 필터링"""
        filtered = self.events
        if start_date:
            filtered = [e for e in filtered
                        if isinstance(e.timestamp, datetime) and e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered
                        if isinstance(e.timestamp, datetime) and e.timestamp <= end_date]
        if event_types:
            filtered = [e for e in filtered if e.event_type in event_types]
        if participants:
            filtered = [
                e for e in filtered
                if any(p in e.participants for p in participants)
            ]
        return filtered

    def update_date_range(self):
        """이벤트 기반으로 날짜 범위 업데이트"""
        timestamps = [e.timestamp for e in self.events if isinstance(e.timestamp, datetime)]
        if timestamps:
            self.date_range_start = min(timestamps).isoformat()
            self.date_range_end = max(timestamps).isoformat()

    def compute_hash(self) -> str:
        """타임라인 해시 계산"""
        event_hashes = [e.hash_value or e.compute_hash() for e in self.events]
        data = f"{self.title}|{'|'.join(event_hashes)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def to_db_dict(self) -> Dict[str, Any]:
        """DB INSERT/UPDATE용 딕셔너리"""
        now = datetime.now().isoformat()
        self.update_date_range()
        return {
            'title': self.title,
            'description': self.description,
            'date_range_start': self.date_range_start,
            'date_range_end': self.date_range_end,
            'source_file': self.source_file,
            'created_at': self.created_at or now,
            'updated_at': now,
            'status': self.status,
            'hash': self.hash or self.compute_hash(),
        }

    @classmethod
    def from_db_row(cls, row: Dict[str, Any], events: Optional[List[TimelineEvent]] = None) -> 'TimelineModel':
        """DB 행에서 생성"""
        created_at = row.get('created_at', '')
        created_date = None
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at)
            except ValueError:
                pass

        return cls(
            id=row.get('id'),
            title=row.get('title', ''),
            description=row.get('description'),
            date_range_start=row.get('date_range_start'),
            date_range_end=row.get('date_range_end'),
            source_file=row.get('source_file'),
            status=row.get('status', 'draft'),
            hash=row.get('hash'),
            created_at=created_at,
            updated_at=row.get('updated_at'),
            events=events or [],
            created_date=created_date,
        )

    def get_timeline_summary(self) -> Dict[str, Any]:
        """타임라인 요약 정보"""
        if not self.events:
            return {
                'event_count': 0,
                'duration_days': 0,
                'participant_count': 0,
                'event_types': [],
                'date_range': None
            }

        return {
            'event_count': self.event_count,
            'duration_days': self.duration,
            'participant_count': self.participant_count,
            'event_types': [et.value for et in self.event_types],
            'date_range': {
                'start': self.date_range_start,
                'end': self.date_range_end,
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """API 응답용 딕셔너리"""
        return {
            'id': self.id,
            'timeline_id': self.timeline_id or (str(self.id) if self.id else None),
            'title': self.title,
            'description': self.description,
            'date_range_start': self.date_range_start,
            'date_range_end': self.date_range_end,
            'source_file': self.source_file,
            'status': self.status,
            'hash': self.hash,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'event_count': self.event_count,
            'events': [e.to_dict() for e in self.events],
            'participants': list(self.participants),
            'event_types': [et.value for et in self.event_types],
            'tags': self.tags,
            'summary': self.get_timeline_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineModel':
        """딕셔너리에서 생성"""
        created_date = None
        if data.get('created_date'):
            created_date = datetime.fromisoformat(data['created_date'])
        elif data.get('created_at'):
            try:
                created_date = datetime.fromisoformat(data['created_at'])
            except ValueError:
                pass

        start_date = None
        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'])
        end_date = None
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'])

        events = []
        for event_data in data.get('events', []):
            if isinstance(event_data, dict):
                timestamp = event_data.get('timestamp', '')
                if isinstance(timestamp, str) and timestamp:
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except ValueError:
                        timestamp = datetime.now()
                elif not timestamp:
                    timestamp = datetime.now()

                et_str = event_data.get('event_type', 'email')
                try:
                    event_type = TimelineEventType(et_str)
                except ValueError:
                    event_type = TimelineEventType.EMAIL

                event = TimelineEvent(
                    id=event_data.get('id'),
                    event_id=event_data.get('event_id'),
                    event_type=event_type,
                    timestamp=timestamp,
                    title=event_data.get('title', ''),
                    description=event_data.get('description'),
                    email_id=event_data.get('email_id'),
                    evidence_id=event_data.get('evidence_id'),
                    participants=event_data.get('participants', []),
                    attachments=event_data.get('attachments', []),
                    metadata=event_data.get('metadata', {}),
                )
                events.append(event)

        event_types_set = set()
        for et_str in data.get('event_types', []):
            try:
                event_types_set.add(TimelineEventType(et_str))
            except ValueError:
                pass

        return cls(
            id=data.get('id'),
            timeline_id=data.get('timeline_id'),
            title=data.get('title', ''),
            created_date=created_date,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            events=events,
            start_date=start_date,
            end_date=end_date,
            date_range_start=data.get('date_range_start'),
            date_range_end=data.get('date_range_end'),
            source_file=data.get('source_file'),
            status=data.get('status', 'draft'),
            hash=data.get('hash'),
            participants=set(data.get('participants', [])),
            event_types=event_types_set,
            description=data.get('description'),
            tags=data.get('tags', []),
        )
