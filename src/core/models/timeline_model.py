"""
Timeline data model for email visualization.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum


class TimelineEventType(Enum):
    """타임라인 이벤트 유형"""
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    EMAIL_REPLIED = "email_replied"
    ATTACHMENT_ADDED = "attachment_added"
    EVIDENCE_CREATED = "evidence_created"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"


@dataclass
class TimelineEvent:
    """타임라인 이벤트"""

    event_id: str
    event_type: TimelineEventType
    timestamp: datetime
    title: str
    description: Optional[str] = None

    # 관련 엔티티
    email_id: Optional[str] = None
    evidence_id: Optional[str] = None

    # 이벤트 속성
    participants: List[str] = None
    attachments: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.participants is None:
            self.participants = []
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TimelineModel:
    """메일 타임라인 데이터 모델"""

    # 타임라인 정보
    timeline_id: str
    title: str
    created_date: datetime

    # 이벤트 목록
    events: List[TimelineEvent] = None

    # 필터링 정보
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    participants: Set[str] = None
    event_types: Set[TimelineEventType] = None

    # 메타데이터
    description: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.events is None:
            self.events = []
        if self.participants is None:
            self.participants = set()
        if self.event_types is None:
            self.event_types = set()
        if self.tags is None:
            self.tags = []

    @property
    def event_count(self) -> int:
        """이벤트 개수"""
        return len(self.events)

    @property
    def duration(self) -> Optional[int]:
        """타임라인 기간 (일)"""
        if not self.events:
            return None

        start = min(event.timestamp for event in self.events)
        end = max(event.timestamp for event in self.events)
        return (end - start).days

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
        self.events.sort(key=lambda x: x.timestamp)

        # 필터 정보 업데이트
        self.participants.update(event.participants)
        self.event_types.add(event.event_type)

    def remove_event(self, event_id: str) -> bool:
        """이벤트 제거"""
        original_count = len(self.events)
        self.events = [e for e in self.events if e.event_id != event_id]
        return len(self.events) < original_count

    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        """이벤트 조회"""
        for event in self.events:
            if event.event_id == event_id:
                return event
        return None

    def get_events_by_date(self, target_date: datetime) -> List[TimelineEvent]:
        """특정 날짜의 이벤트 조회"""
        target_str = target_date.strftime("%Y-%m-%d")
        return [
            event for event in self.events
            if event.timestamp.strftime("%Y-%m-%d") == target_str
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
            filtered = [e for e in filtered if e.timestamp >= start_date]

        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]

        if event_types:
            filtered = [e for e in filtered if e.event_type in event_types]

        if participants:
            filtered = [
                e for e in filtered
                if any(p in e.participants for p in participants)
            ]

        return filtered

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

        start_date = min(event.timestamp for event in self.events)
        end_date = max(event.timestamp for event in self.events)

        return {
            'event_count': self.event_count,
            'duration_days': self.duration,
            'participant_count': self.participant_count,
            'event_types': [et.value for et in self.event_types],
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timeline_id': self.timeline_id,
            'title': self.title,
            'created_date': self.created_date.isoformat(),
            'events': [
                {
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'timestamp': event.timestamp.isoformat(),
                    'title': event.title,
                    'description': event.description,
                    'email_id': event.email_id,
                    'evidence_id': event.evidence_id,
                    'participants': event.participants,
                    'attachments': event.attachments,
                    'metadata': event.metadata
                }
                for event in self.events
            ],
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'participants': list(self.participants),
            'event_types': [et.value for et in self.event_types],
            'description': self.description,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineModel':
        """딕셔너리에서 생성"""
        # 날짜 변환
        created_date = datetime.fromisoformat(data['created_date'])
        start_date = None
        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'])
        end_date = None
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'])

        # 이벤트 변환
        events = []
        for event_data in data.get('events', []):
            event = TimelineEvent(
                event_id=event_data['event_id'],
                event_type=TimelineEventType(event_data['event_type']),
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                title=event_data['title'],
                description=event_data.get('description'),
                email_id=event_data.get('email_id'),
                evidence_id=event_data.get('evidence_id'),
                participants=event_data.get('participants', []),
                attachments=event_data.get('attachments', []),
                metadata=event_data.get('metadata', {})
            )
            events.append(event)

        return cls(
            timeline_id=data['timeline_id'],
            title=data['title'],
            created_date=created_date,
            events=events,
            start_date=start_date,
            end_date=end_date,
            participants=set(data.get('participants', [])),
            event_types={TimelineEventType(et)
                         for et in data.get('event_types', [])},
            description=data.get('description'),
            tags=data.get('tags', [])
        )
