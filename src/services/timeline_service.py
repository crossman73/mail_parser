"""
Timeline service for email visualization
타임라인 시각화 서비스 — DB CRUD + 레거시 인메모리 지원
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.mail_parser.timeline import TimelineBuilder
from src.core.models.timeline_model import (
    TimelineModel,
    TimelineEvent,
    TimelineEventType,
)


class TimelineService:
    """타임라인 서비스 — DB 기반 CRUD + 레거시 호환"""

    def __init__(self):
        """초기화"""
        self.timeline_cache = {}
        self._builder = TimelineBuilder()

    # ─── DB CRUD ──────────────────────────────────────────

    def create_timeline(
        self,
        title: str,
        description: str = None,
        source_file: str = None,
        emails: list = None,
    ) -> Dict[str, Any]:
        """타임라인 생성 및 DB 저장

        Args:
            title: 타임라인 제목
            description: 설명
            source_file: 원본 파일명
            emails: EmailModel 또는 dict 리스트 (선택)

        Returns:
            {'success': bool, 'timeline_id': int, 'message': str}
        """
        try:
            if emails:
                timeline = self._builder.build_from_emails(
                    emails, title=title, source_file=source_file
                )
            else:
                now = datetime.now().isoformat()
                timeline = TimelineModel(
                    title=title,
                    description=description,
                    source_file=source_file,
                    created_at=now,
                    updated_at=now,
                )

            if description:
                timeline.description = description

            tid = self._builder.save_timeline(timeline)
            return {
                'success': True,
                'timeline_id': tid,
                'message': f'타임라인 생성 완료 (이벤트 {timeline.event_count}개)',
            }
        except Exception as e:
            return {'success': False, 'timeline_id': None, 'message': f'생성 오류: {e}'}

    def get_timeline(self, timeline_id: int) -> Optional[Dict[str, Any]]:
        """타임라인 + 이벤트 조회"""
        timeline = self._builder.load_timeline(timeline_id)
        if not timeline:
            return None
        return timeline.to_dict()

    def list_timelines(self, status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """타임라인 목록 조회"""
        return self._builder.list_timelines(status=status, limit=limit)

    def update_timeline_meta(
        self,
        timeline_id: int,
        title: str = None,
        description: str = None,
        status: str = None,
    ) -> Dict[str, Any]:
        """타임라인 메타데이터 수정"""
        timeline = self._builder.load_timeline(timeline_id)
        if not timeline:
            return {'success': False, 'message': '타임라인을 찾을 수 없습니다.'}

        if title is not None:
            timeline.title = title
        if description is not None:
            timeline.description = description
        if status is not None:
            timeline.status = status

        ok = self._builder.update_timeline(timeline)
        return {
            'success': ok,
            'message': '수정 완료' if ok else '수정 실패',
        }

    def delete_timeline(self, timeline_id: int) -> Dict[str, Any]:
        """타임라인 삭제"""
        ok = self._builder.delete_timeline(timeline_id)
        return {
            'success': ok,
            'message': '삭제 완료' if ok else '삭제 실패',
        }

    # ─── 이벤트 CRUD ──────────────────────────────────────

    def create_event(
        self,
        timeline_id: int,
        title: str,
        timestamp: str,
        event_type: str = 'email',
        description: str = None,
        email_id: str = None,
        evidence_id: int = None,
        source_file: str = None,
        participants: list = None,
        attachments: list = None,
        legal_significance: str = None,
        notes: str = None,
        is_key_event: bool = False,
    ) -> Dict[str, Any]:
        """이벤트 추가"""
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return {'success': False, 'event_id': None, 'message': '잘못된 날짜 형식'}

        try:
            et = TimelineEventType(event_type)
        except ValueError:
            et = TimelineEventType.EMAIL

        event = TimelineEvent(
            timestamp=ts,
            title=title,
            event_type=et,
            description=description,
            email_id=email_id,
            evidence_id=evidence_id,
            source_file=source_file or '',
            participants=participants or [],
            attachments=attachments or [],
            legal_significance=legal_significance,
            notes=notes,
            is_key_event=is_key_event,
        )

        eid = self._builder.add_event(timeline_id, event)
        return {
            'success': True,
            'event_id': eid,
            'message': '이벤트 추가 완료',
        }

    def update_event(
        self,
        event_id: int,
        **kwargs,
    ) -> Dict[str, Any]:
        """이벤트 수정"""
        event = self._builder.get_event(event_id)
        if not event:
            return {'success': False, 'message': '이벤트를 찾을 수 없습니다.'}

        # 업데이트 가능한 필드
        updatable = [
            'title', 'description', 'legal_significance', 'notes',
            'is_key_event', 'sort_order', 'verified',
        ]
        for key in updatable:
            if key in kwargs:
                setattr(event, key, kwargs[key])

        if 'timestamp' in kwargs:
            try:
                event.timestamp = datetime.fromisoformat(kwargs['timestamp'])
            except (ValueError, TypeError):
                pass

        if 'event_type' in kwargs:
            try:
                event.event_type = TimelineEventType(kwargs['event_type'])
            except ValueError:
                pass

        if 'participants' in kwargs:
            event.participants = kwargs['participants'] or []
        if 'attachments' in kwargs:
            event.attachments = kwargs['attachments'] or []

        ok = self._builder.update_event(event)
        return {
            'success': ok,
            'message': '이벤트 수정 완료' if ok else '수정 실패',
        }

    def delete_event(self, event_id: int, timeline_id: int = None) -> Dict[str, Any]:
        """이벤트 삭제"""
        ok = self._builder.delete_event(event_id, timeline_id=timeline_id)
        return {
            'success': ok,
            'message': '이벤트 삭제 완료' if ok else '삭제 실패',
        }

    def reorder_events(self, timeline_id: int, event_ids: List[int]) -> Dict[str, Any]:
        """이벤트 순서 변경"""
        ok = self._builder.reorder_events(timeline_id, event_ids)
        return {
            'success': ok,
            'message': '순서 변경 완료' if ok else '순서 변경 실패',
        }

    # ─── 레거시 메서드 (기존 라우트 호환) ─────────────────

    def generate_timeline_from_evidence(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """증거 목록으로부터 타임라인 생성"""
        if not evidence_list:
            return {
                'success': False,
                'message': '증거 목록이 비어있습니다.',
                'timeline': {}
            }

        try:
            # 날짜별로 이벤트 그룹화
            events_by_date = defaultdict(list)

            for evidence in evidence_list:
                try:
                    # 날짜 파싱
                    date_str = evidence.get('date', '')
                    if not date_str:
                        continue

                    # 다양한 날짜 형식 처리
                    parsed_date = self._parse_date(date_str)
                    if not parsed_date:
                        continue

                    date_key = parsed_date.strftime('%Y-%m-%d')

                    # 이벤트 생성
                    event = {
                        'id': evidence.get('folder_name', ''),
                        'title': evidence.get('title', '제목없음'),
                        'evidence_number': evidence.get('evidence_number', ''),
                        'time': parsed_date.strftime('%H:%M') if parsed_date.hour or parsed_date.minute else '00:00',
                        'folder_path': evidence.get('folder_path', ''),
                        'attachment_count': evidence.get('attachment_count', 0),
                        'html_files': evidence.get('html_files', 0),
                        'pdf_files': evidence.get('pdf_files', 0),
                        'type': 'evidence'
                    }

                    events_by_date[date_key].append(event)

                except Exception as e:
                    print(f"이벤트 생성 오류: {e}")
                    continue

            # 날짜순 정렬
            sorted_dates = sorted(events_by_date.keys())

            # 타임라인 데이터 구성
            timeline_data = {
                'title': f'이메일 증거 타임라인 ({len(evidence_list)}개 증거)',
                'date_range': {
                    'start': sorted_dates[0] if sorted_dates else None,
                    'end': sorted_dates[-1] if sorted_dates else None
                },
                'total_events': len(evidence_list),
                'events_by_date': dict(events_by_date),
                'statistics': self._calculate_timeline_statistics(events_by_date)
            }

            return {
                'success': True,
                'message': f'{len(sorted_dates)}일간의 타임라인이 생성되었습니다.',
                'timeline': timeline_data
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'타임라인 생성 오류: {str(e)}',
                'timeline': {}
            }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """다양한 날짜 형식 파싱"""
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y.%m.%d',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # RFC 2822 형식 시도
        try:
            import email.utils
            return email.utils.parsedate_to_datetime(date_str)
        except (TypeError, ValueError):
            # Invalid date format - return None
            return None
        except Exception as e:
            print(f"⚠️ RFC 2822 날짜 파싱 실패: {date_str} - {e}")
            return None

    def _calculate_timeline_statistics(self, events_by_date: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """타임라인 통계 계산"""
        if not events_by_date:
            return {}

        # 일별 이벤트 수
        daily_counts = {date: len(events)
                        for date, events in events_by_date.items()}

        # 가장 바쁜 날
        busiest_date = max(daily_counts.items(), key=lambda x: x[1])

        # 증거 유형별 통계
        evidence_types = {'갑': 0, '을': 0, '기타': 0}
        total_attachments = 0

        for events in events_by_date.values():
            for event in events:
                evidence_num = event.get('evidence_number', '')
                if evidence_num.startswith('갑'):
                    evidence_types['갑'] += 1
                elif evidence_num.startswith('을'):
                    evidence_types['을'] += 1
                else:
                    evidence_types['기타'] += 1

                total_attachments += event.get('attachment_count', 0)

        return {
            'total_days': len(events_by_date),
            'daily_average': sum(daily_counts.values()) / len(daily_counts),
            'busiest_day': {
                'date': busiest_date[0],
                'count': busiest_date[1]
            },
            'evidence_types': evidence_types,
            'total_attachments': total_attachments
        }

    def filter_timeline(self, timeline_data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """타임라인 필터링"""
        if not timeline_data.get('events_by_date'):
            return timeline_data

        try:
            filtered_events = {}

            # 날짜 범위 필터
            start_date = filters.get('start_date')
            end_date = filters.get('end_date')

            # 증거 유형 필터
            evidence_types = filters.get('evidence_types', [])

            # 키워드 필터
            keyword = filters.get('keyword', '').lower()

            for date, events in timeline_data['events_by_date'].items():
                # 날짜 범위 확인
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue

                filtered_day_events = []

                for event in events:
                    # 증거 유형 필터
                    if evidence_types:
                        evidence_num = event.get('evidence_number', '')
                        if not any(evidence_num.startswith(et) for et in evidence_types):
                            continue

                    # 키워드 필터
                    if keyword:
                        title = event.get('title', '').lower()
                        if keyword not in title:
                            continue

                    filtered_day_events.append(event)

                if filtered_day_events:
                    filtered_events[date] = filtered_day_events

            # 필터링된 결과로 타임라인 업데이트
            filtered_timeline = timeline_data.copy()
            filtered_timeline['events_by_date'] = filtered_events
            filtered_timeline['total_events'] = sum(
                len(events) for events in filtered_events.values())
            filtered_timeline['statistics'] = self._calculate_timeline_statistics(
                filtered_events)

            return filtered_timeline

        except Exception as e:
            print(f"타임라인 필터링 오류: {e}")
            return timeline_data

    def export_timeline(self, timeline_data: Dict[str, Any], output_format: str = 'json') -> str:
        """타임라인 내보내기"""
        try:
            if output_format.lower() == 'json':
                return json.dumps(timeline_data, ensure_ascii=False, indent=2)

            elif output_format.lower() == 'csv':
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)

                # 헤더
                writer.writerow(['날짜', '시간', '제목', '증거번호', '첨부파일수', '폴더경로'])

                # 데이터
                events_by_date = timeline_data.get('events_by_date', {})
                for date in sorted(events_by_date.keys()):
                    for event in events_by_date[date]:
                        writer.writerow([
                            date,
                            event.get('time', '00:00'),
                            event.get('title', ''),
                            event.get('evidence_number', ''),
                            event.get('attachment_count', 0),
                            event.get('folder_path', '')
                        ])

                return output.getvalue()

            elif output_format.lower() == 'html':
                return self._generate_timeline_html(timeline_data)

            return ""

        except Exception as e:
            return f"내보내기 오류: {str(e)}"

    def _generate_timeline_html(self, timeline_data: Dict[str, Any]) -> str:
        """타임라인 HTML 생성"""
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 20px; }}
                .timeline-header {{ text-align: center; margin-bottom: 30px; }}
                .timeline {{ position: relative; padding: 20px 0; }}
                .timeline-item {{ margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-left: 4px solid #007bff; }}
                .timeline-date {{ font-size: 18px; font-weight: bold; color: #007bff; margin-bottom: 15px; }}
                .event {{ margin-bottom: 15px; padding: 10px; background: white; border-radius: 5px; }}
                .event-title {{ font-weight: bold; color: #333; }}
                .event-details {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .statistics {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="timeline-header">
                <h1>{title}</h1>
                <p>기간: {date_range}</p>
                <p>총 {total_events}개 이벤트</p>
            </div>

            <div class="timeline">
                {timeline_content}
            </div>

            <div class="statistics">
                <h3>통계 정보</h3>
                {statistics_content}
            </div>
        </body>
        </html>
        """

        # 타임라인 내용 생성
        timeline_content = ""
        events_by_date = timeline_data.get('events_by_date', {})

        for date in sorted(events_by_date.keys()):
            events = events_by_date[date]
            timeline_content += '<div class="timeline-item">'
            timeline_content += f'<div class="timeline-date">{date} ({len(events)}개 이벤트)</div>'

            for event in events:
                timeline_content += '<div class="event">'
                timeline_content += f'<div class="event-title">{event.get("evidence_number", "")} - {event.get("title", "")}</div>'
                timeline_content += f'<div class="event-details">시간: {event.get("time", "00:00")} | 첨부파일: {event.get("attachment_count", 0)}개</div>'
                timeline_content += '</div>'

            timeline_content += '</div>'

        # 통계 내용 생성
        stats = timeline_data.get('statistics', {})
        statistics_content = f"""
        <p>총 기간: {stats.get('total_days', 0)}일</p>
        <p>일평균 이벤트: {stats.get('daily_average', 0):.1f}개</p>
        <p>가장 바쁜 날: {stats.get('busiest_day', {}).get('date', 'N/A')} ({stats.get('busiest_day', {}).get('count', 0)}개 이벤트)</p>
        """

        return html_template.format(
            title=timeline_data.get('title', '타임라인'),
            date_range=f"{timeline_data.get('date_range', {}).get('start', 'N/A')} ~ {timeline_data.get('date_range', {}).get('end', 'N/A')}",
            total_events=timeline_data.get('total_events', 0),
            timeline_content=timeline_content,
            statistics_content=statistics_content
        )

    def get_timeline_summary(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """타임라인 요약 정보"""
        if not timeline_data:
            return {}

        events_by_date = timeline_data.get('events_by_date', {})
        stats = timeline_data.get('statistics', {})

        return {
            'total_events': timeline_data.get('total_events', 0),
            'total_days': len(events_by_date),
            'date_range': timeline_data.get('date_range', {}),
            'daily_average': stats.get('daily_average', 0),
            'evidence_distribution': stats.get('evidence_types', {}),
            'busiest_day': stats.get('busiest_day', {}),
            'total_attachments': stats.get('total_attachments', 0)
        }
