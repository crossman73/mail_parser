"""
Email service for handling email processing operations
웹 인터페이스와 메일 처리 로직 연결
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..mail_parser.processor import EmailEvidenceProcessor


class EmailService:
    """이메일 처리 서비스"""

    def __init__(self, config_path: str = "config.json"):
        """초기화"""
        self.config_path = config_path
        self.processor = None
        self.processed_emails = []

    def load_mbox(self, mbox_path: str) -> Dict[str, Any]:
        """mbox 파일 로드"""
        try:
            self.processor = EmailEvidenceProcessor(self.config_path)
            success = self.processor.load_mbox(mbox_path)

            if success:
                # 이메일 목록 추출 (미리보기용)
                emails_preview = self._get_emails_preview()
                return {
                    'success': True,
                    'message': 'mbox 파일이 성공적으로 로드되었습니다.',
                    'email_count': len(emails_preview),
                    'emails': emails_preview
                }
            else:
                return {
                    'success': False,
                    'message': 'mbox 파일 로드에 실패했습니다.',
                    'email_count': 0,
                    'emails': []
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'오류 발생: {str(e)}',
                'email_count': 0,
                'emails': []
            }

    def _get_emails_preview(self, limit: int = 100) -> List[Dict[str, Any]]:
        """이메일 미리보기 목록 생성"""
        if not self.processor or not self.processor.mbox:
            return []

        preview_emails = []
        count = 0

        for message in self.processor.mbox:
            if count >= limit:
                break

            try:
                # 기본 정보만 추출
                subject = self.processor._decode_text(
                    message.get('Subject', '(제목없음)'))
                sender = message.get('From', '')
                date_str = message.get('Date', '')

                # 날짜 파싱
                try:
                    import email.utils
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = parsed_date.strftime('%Y-%m-%d %H:%M')
                except:
                    date_formatted = date_str

                # 첨부파일 개수 확인
                attachment_count = 0
                if message.is_multipart():
                    for part in message.walk():
                        if part.get('Content-Disposition') and 'attachment' in part.get('Content-Disposition'):
                            attachment_count += 1

                preview_emails.append({
                    'index': count,
                    'subject': subject,
                    'sender': sender,
                    'date': date_formatted,
                    'attachment_count': attachment_count,
                    'selected': False  # 웹 UI용
                })

                count += 1

            except Exception as e:
                print(f"이메일 미리보기 생성 오류: {e}")
                continue

        return preview_emails

    def process_selected_emails(self, selected_indices: List[int]) -> Dict[str, Any]:
        """선택된 이메일들 처리"""
        if not self.processor:
            return {
                'success': False,
                'message': 'mbox 파일이 로드되지 않았습니다.',
                'processed_count': 0
            }

        try:
            processed_count = 0
            errors = []

            # 선택된 이메일들만 처리
            for i, message in enumerate(self.processor.mbox):
                if i in selected_indices:
                    try:
                        # 개별 이메일 처리
                        result = self.processor.process_single_email(
                            message, i)
                        if result:
                            processed_count += 1
                        else:
                            errors.append(f"인덱스 {i}: 처리 실패")
                    except Exception as e:
                        errors.append(f"인덱스 {i}: {str(e)}")

            return {
                'success': processed_count > 0,
                'message': f'{processed_count}개 이메일이 성공적으로 처리되었습니다.',
                'processed_count': processed_count,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'처리 중 오류 발생: {str(e)}',
                'processed_count': 0
            }

    def get_processing_status(self) -> Dict[str, Any]:
        """처리 상태 조회"""
        if not self.processor:
            return {
                'status': 'not_loaded',
                'message': 'mbox 파일이 로드되지 않았습니다.',
                'progress': 0
            }

        # 프로세서의 진행 상태 확인
        return {
            'status': 'ready',
            'message': '처리 준비 완료',
            'progress': 0,
            'total_emails': len(list(self.processor.mbox)) if self.processor.mbox else 0
        }

    def get_email_statistics(self) -> Dict[str, Any]:
        """이메일 통계 정보"""
        if not self.processor or not self.processor.mbox:
            return {
                'total_count': 0,
                'with_attachments': 0,
                'date_range': None,
                'sender_stats': {}
            }

        try:
            total_count = 0
            with_attachments = 0
            sender_stats = {}
            dates = []

            for message in self.processor.mbox:
                total_count += 1

                # 발신자 통계
                sender = message.get('From', 'Unknown')
                sender_stats[sender] = sender_stats.get(sender, 0) + 1

                # 첨부파일 확인
                if message.is_multipart():
                    for part in message.walk():
                        if part.get('Content-Disposition') and 'attachment' in part.get('Content-Disposition'):
                            with_attachments += 1
                            break

                # 날짜 수집
                date_str = message.get('Date', '')
                if date_str:
                    try:
                        import email.utils
                        parsed_date = email.utils.parsedate_to_datetime(
                            date_str)
                        dates.append(parsed_date)
                    except:
                        pass

            # 날짜 범위 계산
            date_range = None
            if dates:
                dates.sort()
                date_range = {
                    'start': dates[0].strftime('%Y-%m-%d'),
                    'end': dates[-1].strftime('%Y-%m-%d')
                }

            return {
                'total_count': total_count,
                'with_attachments': with_attachments,
                'attachment_rate': (with_attachments / total_count * 100) if total_count > 0 else 0,
                'date_range': date_range,
                'sender_stats': dict(sorted(sender_stats.items(), key=lambda x: x[1], reverse=True)[:10])
            }

        except Exception as e:
            print(f"통계 생성 오류: {e}")
            return {
                'total_count': 0,
                'with_attachments': 0,
                'date_range': None,
                'sender_stats': {}
            }

    def search_emails(self, keyword: str, field: str = 'all') -> List[Dict[str, Any]]:
        """이메일 검색"""
        if not self.processor or not self.processor.mbox:
            return []

        results = []
        keyword_lower = keyword.lower()

        for i, message in enumerate(self.processor.mbox):
            try:
                match = False

                if field == 'all' or field == 'subject':
                    subject = self.processor._decode_text(
                        message.get('Subject', ''))
                    if keyword_lower in subject.lower():
                        match = True

                if field == 'all' or field == 'sender':
                    sender = message.get('From', '')
                    if keyword_lower in sender.lower():
                        match = True

                if field == 'all' or field == 'content':
                    # 본문 검색 (간단 구현)
                    if message.is_multipart():
                        for part in message.walk():
                            if part.get_content_type() == 'text/plain':
                                try:
                                    content = part.get_payload(decode=True).decode(
                                        'utf-8', errors='ignore')
                                    if keyword_lower in content.lower():
                                        match = True
                                        break
                                except:
                                    pass

                if match:
                    subject = self.processor._decode_text(
                        message.get('Subject', '(제목없음)'))
                    sender = message.get('From', '')
                    date_str = message.get('Date', '')

                    results.append({
                        'index': i,
                        'subject': subject,
                        'sender': sender,
                        'date': date_str,
                        'matched_field': field
                    })

            except Exception as e:
                print(f"검색 오류 (인덱스 {i}): {e}")
                continue

        return results[:100]  # 최대 100개 결과
