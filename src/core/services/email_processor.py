"""
Email processing service for evidence creation.
"""

import json
import mailbox
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models import EmailModel, AttachmentModel
from ..utils import decode_text, get_email_date, sanitize_filename
from .integrity_service import IntegrityService


class EmailProcessor:
    """메일 처리 서비스"""

    def __init__(self, config_path: str):
        """초기화"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.mbox = None
        self.integrity_service = IntegrityService()
        self.processed_emails: List[EmailModel] = []

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"설정 파일 로드 실패: {e}")

    def load_mbox(self, mbox_path: str) -> bool:
        """mbox 파일 로드"""
        try:
            self.mbox = mailbox.mbox(mbox_path)
            return True
        except Exception as e:
            print(f"mbox 파일 로드 실패: {e}")
            return False

    def parse_email(self, message) -> EmailModel:
        """이메일 메시지를 EmailModel로 변환"""

        # 메시지 ID 생성
        message_id = message.get('Message-ID', '')
        if not message_id:
            # 메시지 ID가 없으면 생성
            import hashlib
            content = str(message)
            message_id = hashlib.md5(content.encode()).hexdigest()

        # 기본 정보 추출
        subject = decode_text(message.get('Subject', '(제목없음)'))
        sender = message.get('From', '')
        recipients = []

        # 수신자 정보 처리
        to_header = message.get('To', '')
        cc_header = message.get('Cc', '')
        if to_header:
            recipients.extend(re.findall(r'[\\w\\.-]+@[\\w\\.-]+', to_header))
        if cc_header:
            recipients.extend(re.findall(r'[\\w\\.-]+@[\\w\\.-]+', cc_header))

        # 날짜 처리
        email_date = get_email_date(message)

        # 본문 추출
        body_text = None
        body_html = None
        attachments = []

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = part.get('Content-Disposition', '')

                if 'attachment' in content_disposition:
                    # 첨부파일 처리
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
                elif content_type == 'text/plain' and not body_text:
                    try:
                        body_text = part.get_payload(
                            decode=True).decode('utf-8')
                    except:
                        pass
                elif content_type == 'text/html' and not body_html:
                    try:
                        body_html = part.get_payload(
                            decode=True).decode('utf-8')
                    except:
                        pass
        else:
            # 단일 파트 메시지
            try:
                content = message.get_payload(decode=True)
                if content:
                    body_text = content.decode('utf-8')
            except:
                pass

        # 스레드 정보
        thread_id = message.get('Thread-Topic')
        in_reply_to = message.get('In-Reply-To')
        references = []
        references_header = message.get('References', '')
        if references_header:
            references = re.findall(r'<[^>]+>', references_header)

        # 무결성 해시 계산
        original_hash = self.integrity_service.calculate_message_hash(
            str(message))

        return EmailModel(
            message_id=message_id,
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=email_date,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            thread_id=thread_id,
            in_reply_to=in_reply_to,
            references=references,
            original_hash=original_hash
        )

    def extract_attachments(self, message, email_model: EmailModel, output_dir: Path) -> List[AttachmentModel]:
        """첨부파일 추출"""
        attachments = []
        attachment_dir = output_dir / "attachments"
        attachment_dir.mkdir(exist_ok=True)

        if not message.is_multipart():
            return attachments

        attachment_count = 0
        for part in message.walk():
            content_disposition = part.get('Content-Disposition', '')
            if 'attachment' not in content_disposition:
                continue

            filename = part.get_filename()
            if not filename:
                continue

            try:
                # 파일명 정리
                clean_filename = sanitize_filename(decode_text(filename))

                # 중복 방지
                attachment_count += 1
                if attachment_count > 1:
                    name, ext = clean_filename.rsplit(
                        '.', 1) if '.' in clean_filename else (clean_filename, '')
                    clean_filename = f"{name}_{attachment_count}.{ext}" if ext else f"{clean_filename}_{attachment_count}"

                file_path = attachment_dir / clean_filename

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))

                # AttachmentModel 생성
                attachment_id = f"{email_model.message_id}_{attachment_count}"
                attachment_model = AttachmentModel.create_from_file(
                    attachment_id=attachment_id,
                    file_path=file_path,
                    email_message_id=email_model.message_id,
                    email_subject=email_model.subject,
                    original_filename=filename,
                    is_inline=part.get('Content-ID') is not None,
                    content_id=part.get('Content-ID')
                )

                # 해시 계산
                attachment_model.calculate_hash()

                attachments.append(attachment_model)

            except Exception as e:
                print(f"첨부파일 추출 오류 ({filename}): {e}")
                continue

        return attachments

    def filter_emails(self, emails: List[EmailModel]) -> List[EmailModel]:
        """설정에 따른 이메일 필터링"""
        if not self.config.get('filters'):
            return emails

        filtered = emails
        filters = self.config['filters']

        # 날짜 범위 필터
        if filters.get('date_range'):
            date_range = filters['date_range']
            start_date = datetime.fromisoformat(
                date_range['start']) if date_range.get('start') else None
            end_date = datetime.fromisoformat(
                date_range['end']) if date_range.get('end') else None

            if start_date:
                filtered = [e for e in filtered if e.date >= start_date]
            if end_date:
                filtered = [e for e in filtered if e.date <= end_date]

        # 발신자 필터
        if filters.get('senders'):
            senders = set(filters['senders'])
            filtered = [e for e in filtered if any(
                sender in e.sender for sender in senders)]

        # 제목 키워드 필터
        if filters.get('subject_keywords'):
            keywords = filters['subject_keywords']
            filtered = [
                e for e in filtered
                if any(keyword.lower() in e.subject.lower() for keyword in keywords)
            ]

        # 첨부파일 필터
        if filters.get('has_attachments'):
            filtered = [e for e in filtered if e.attachment_count > 0]

        return filtered

    def process_all_emails(self) -> List[EmailModel]:
        """모든 이메일 처리"""
        if not self.mbox:
            raise Exception("mbox 파일이 로드되지 않았습니다.")

        emails = []
        total_count = len(self.mbox)

        for i, message in enumerate(self.mbox):
            try:
                email_model = self.parse_email(message)
                emails.append(email_model)

                if (i + 1) % 10 == 0:
                    print(f"처리 진행률: {i + 1}/{total_count}")

            except Exception as e:
                print(f"이메일 처리 오류 (인덱스 {i}): {e}")
                continue

        # 필터링 적용
        filtered_emails = self.filter_emails(emails)

        # 날짜순 정렬
        filtered_emails.sort(key=lambda x: x.date)

        self.processed_emails = filtered_emails
        return filtered_emails

    def get_email_statistics(self) -> Dict[str, Any]:
        """이메일 통계 정보"""
        if not self.processed_emails:
            return {}

        total_count = len(self.processed_emails)
        with_attachments = len(
            [e for e in self.processed_emails if e.attachment_count > 0])

        # 발신자별 통계
        sender_stats = {}
        for email in self.processed_emails:
            sender = email.sender
            sender_stats[sender] = sender_stats.get(sender, 0) + 1

        # 날짜별 통계
        date_stats = {}
        for email in self.processed_emails:
            date_str = email.date_str
            date_stats[date_str] = date_stats.get(date_str, 0) + 1

        return {
            'total_count': total_count,
            'with_attachments': with_attachments,
            'attachment_rate': with_attachments / total_count * 100 if total_count > 0 else 0,
            'sender_stats': sender_stats,
            'date_stats': date_stats,
            'date_range': {
                'start': min(e.date for e in self.processed_emails).isoformat(),
                'end': max(e.date for e in self.processed_emails).isoformat()
            }
        }
