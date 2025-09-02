"""
Timeline generation service for email visualization.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models import EmailModel, EvidenceModel, TimelineModel, TimelineEvent, TimelineEventType


class TimelineGenerator:
    """타임라인 생성 서비스"""

    def __init__(self):
        """초기화"""
        self.timelines: Dict[str, TimelineModel] = {}

    def create_timeline(self, title: str, emails: List[EmailModel]) -> TimelineModel:
        """이메일 목록으로부터 타임라인 생성"""
        timeline_id = str(uuid.uuid4())

        timeline = TimelineModel(
            timeline_id=timeline_id,
            title=title,
            created_date=datetime.now()
        )

        # 이메일을 이벤트로 변환
        for email in emails:
            self._add_email_events(timeline, email)

        self.timelines[timeline_id] = timeline
        return timeline

    def _add_email_events(self, timeline: TimelineModel, email: EmailModel):
        """이메일을 타임라인 이벤트로 추가"""

        # 메일 전송/수신 이벤트
        event_type = TimelineEventType.EMAIL_SENT  # 기본값

        # 답장 여부 확인
        if email.in_reply_to:
            event_type = TimelineEventType.EMAIL_REPLIED

        # 기본 이메일 이벤트
        email_event = TimelineEvent(
            event_id=f"email_{email.message_id}",
            event_type=event_type,
            timestamp=email.date,
            title=email.subject,
            description=f"발신자: {email.sender}",
            email_id=email.message_id,
            participants=[email.sender] + email.recipients,
            attachments=email.attachments,
            metadata={
                'message_id': email.message_id,
                'reply_to': email.in_reply_to,
                'thread_id': email.thread_id,
                'attachment_count': email.attachment_count
            }
        )

        timeline.add_event(email_event)

        # 첨부파일이 있는 경우 별도 이벤트 추가
        if email.attachments:
            attachment_event = TimelineEvent(
                event_id=f"attachment_{email.message_id}",
                event_type=TimelineEventType.ATTACHMENT_ADDED,
                timestamp=email.date,
                title=f"첨부파일 {len(email.attachments)}개",
                description=f"첨부파일: {', '.join(email.attachments[:3])}{'...' if len(email.attachments) > 3 else ''}",
                email_id=email.message_id,
                participants=[email.sender],
                attachments=email.attachments,
                metadata={
                    'attachment_count': len(email.attachments),
                    'attachment_names': email.attachments
                }
            )

            timeline.add_event(attachment_event)

    def add_evidence_event(self, timeline_id: str, evidence: EvidenceModel):
        """증거 생성 이벤트 추가"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return

        evidence_event = TimelineEvent(
            event_id=f"evidence_{evidence.evidence_id}",
            event_type=TimelineEventType.EVIDENCE_CREATED,
            timestamp=evidence.created_date,
            title=f"{evidence.evidence_label} 생성",
            description=f"증거 생성: {evidence.email_subject}",
            email_id=evidence.email_message_id,
            evidence_id=evidence.evidence_id,
            metadata={
                'evidence_type': evidence.evidence_type.value,
                'evidence_sequence': evidence.evidence_sequence,
                'evidence_label': evidence.evidence_label
            }
        )

        timeline.add_event(evidence_event)

    def add_processing_events(self, timeline_id: str, email: EmailModel):
        """처리 관련 이벤트 추가"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return

        # 처리 시작 이벤트
        if email.processed_date:
            start_event = TimelineEvent(
                event_id=f"process_start_{email.message_id}",
                event_type=TimelineEventType.PROCESSING_STARTED,
                timestamp=email.processed_date,
                title="처리 시작",
                description=f"이메일 처리 시작: {email.subject}",
                email_id=email.message_id,
                metadata={
                    'processing_type': 'evidence_generation'
                }
            )

            timeline.add_event(start_event)

            # 처리 완료 이벤트
            complete_event = TimelineEvent(
                event_id=f"process_complete_{email.message_id}",
                event_type=TimelineEventType.PROCESSING_COMPLETED,
                timestamp=email.processed_date,
                title="처리 완료",
                description=f"증거 생성 완료: {email.evidence_number}",
                email_id=email.message_id,
                metadata={
                    'evidence_number': email.evidence_number,
                    'output_files': [str(email.html_path), str(email.pdf_path)]
                }
            )

            timeline.add_event(complete_event)

    def get_timeline(self, timeline_id: str) -> Optional[TimelineModel]:
        """타임라인 조회"""
        return self.timelines.get(timeline_id)

    def get_timeline_data_for_web(self, timeline_id: str) -> Dict[str, Any]:
        """웹 인터페이스용 타임라인 데이터"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return {}

        # 이벤트를 날짜별로 그룹화
        events_by_date = {}
        for event in timeline.events:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append({
                'id': event.event_id,
                'type': event.event_type.value,
                'time': event.timestamp.strftime("%H:%M:%S"),
                'title': event.title,
                'description': event.description,
                'participants': event.participants,
                'attachments': event.attachments,
                'metadata': event.metadata
            })

        # 날짜순 정렬
        sorted_dates = sorted(events_by_date.keys())

        return {
            'timeline_id': timeline_id,
            'title': timeline.title,
            'created_date': timeline.created_date.isoformat(),
            'summary': timeline.get_timeline_summary(),
            'events_by_date': {
                date: events_by_date[date] for date in sorted_dates
            },
            'total_events': timeline.event_count,
            'date_range': sorted_dates[0] + ' ~ ' + sorted_dates[-1] if sorted_dates else ''
        }

    def filter_timeline_events(
        self,
        timeline_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        participants: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """타임라인 이벤트 필터링"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return []

        # 필터 조건 변환
        filter_event_types = None
        if event_types:
            filter_event_types = [TimelineEventType(et) for et in event_types]

        # 필터링된 이벤트
        filtered_events = timeline.filter_events(
            start_date=start_date,
            end_date=end_date,
            event_types=filter_event_types,
            participants=participants
        )

        # 웹용 데이터로 변환
        return [
            {
                'id': event.event_id,
                'type': event.event_type.value,
                'timestamp': event.timestamp.isoformat(),
                'title': event.title,
                'description': event.description,
                'participants': event.participants,
                'attachments': event.attachments,
                'metadata': event.metadata
            }
            for event in filtered_events
        ]

    def export_timeline(self, timeline_id: str, format: str = 'json') -> str:
        """타임라인 내보내기"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return ""

        if format.lower() == 'json':
            import json
            return json.dumps(timeline.to_dict(), ensure_ascii=False, indent=2)

        elif format.lower() == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # 헤더
            writer.writerow([
                '날짜', '시간', '이벤트 유형', '제목', '설명', '참여자', '첨부파일'
            ])

            # 데이터
            for event in timeline.events:
                writer.writerow([
                    event.timestamp.strftime("%Y-%m-%d"),
                    event.timestamp.strftime("%H:%M:%S"),
                    event.event_type.value,
                    event.title,
                    event.description or '',
                    '; '.join(event.participants),
                    '; '.join(event.attachments) if event.attachments else ''
                ])

            return output.getvalue()

        return ""

    def get_statistics(self, timeline_id: str) -> Dict[str, Any]:
        """타임라인 통계"""
        timeline = self.timelines.get(timeline_id)
        if not timeline:
            return {}

        # 이벤트 유형별 통계
        event_type_counts = {}
        for event in timeline.events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(
                event_type, 0) + 1

        # 참여자별 통계
        participant_counts = {}
        for event in timeline.events:
            for participant in event.participants:
                participant_counts[participant] = participant_counts.get(
                    participant, 0) + 1

        # 일별 이벤트 수
        daily_counts = {}
        for event in timeline.events:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        return {
            'timeline_summary': timeline.get_timeline_summary(),
            'event_type_distribution': event_type_counts,
            'participant_activity': dict(sorted(participant_counts.items(), key=lambda x: x[1], reverse=True)),
            'daily_event_counts': dict(sorted(daily_counts.items())),
            'busiest_day': max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        }
