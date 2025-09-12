# src/mail_parser/processor.py

import base64
import json
import mailbox
import os
import re
import shutil
from datetime import datetime
from email.message import Message
from typing import Any, Dict, List, Optional, cast

from src.parser.mailbox_processor import process_mailbox

from .analyzer import ThreadAnalyzer
from .evidence_generator import EvidenceGenerator
from .forensic_integrity import ForensicIntegrityService
from .formatter import CourtFormatter
from .integrity import IntegrityManager
from .logger import (log_email_processing, log_file_operation,
                     log_processing_step, setup_logger)
from .streaming_processor import StreamingEmailProcessor
from .utils import decode_text, get_email_date, sanitize_filename

OUTPUT_DIR = 'processed_emails'


class EmailEvidenceProcessor:
    def __init__(self, config_path):
        # 로깅 시스템 초기화
        self.logger = setup_logger('EmailEvidenceProcessor')
        self.logger.info(f"프로세서 초기화 시작 (설정 파일: {config_path})")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            log_file_operation(self.logger, '설정 파일 로드',
                               config_path, success=True)
        except Exception as e:
            log_file_operation(self.logger, '설정 파일 로드',
                               config_path, success=False, error_msg=str(e))
            raise

        # mbox can be mailbox.mbox or a synthetic mapping produced by the
        # threaded loader; keep as Any to avoid static type complaints.
        self.mbox: Any = None
        self.formatter = CourtFormatter()
        self.integrity_manager = IntegrityManager()
        self.forensic_service = ForensicIntegrityService()
        self.streaming_processor = StreamingEmailProcessor(
            chunk_size_mb=self.config.get(
                'processing_options', {}).get('chunk_size_mb', 64),
            streaming_threshold_mb=self.config.get(
                'processing_options', {}).get('streaming_threshold_mb', 500)
        )
        self.evidence_counter: Dict[str, int] = {}
        # metadata_map: message-id -> metadata dict
        self.metadata_map: Dict[str, Dict[str, Any]] = {}
        # feature flag: use thread-based mailbox loader (experimental)
        self.use_threaded_loader: bool = self.config.get(
            'processing_options', {}).get('use_threaded_loader', False)
        self.evidence_generator = EvidenceGenerator(self)

        log_processing_step(self.logger, '초기화', '프로세서 초기화 완료')

    def load_mbox(self, mbox_path: str) -> None:
        log_processing_step(self.logger, 1, f"mbox 파일 로드 시작: {mbox_path}")

        # If experimental flag is enabled, use the thread-based loader which
        # returns grouped Message objects; this allows a gradual rollout.
        if self.use_threaded_loader:
            self.load_mbox_as_threads(mbox_path)
            return

        # Default: keep original mailbox.mbox behavior for compatibility
        try:
            self.mbox = mailbox.mbox(mbox_path)
            log_file_operation(self.logger, 'mbox 로드', mbox_path, success=True)
        except Exception as e:
            log_file_operation(self.logger, 'mbox 로드',
                               mbox_path, success=False, error_msg=str(e))
            raise

        log_processing_step(self.logger, 2, f"메타데이터 수집 시작")
        metadata_count = 0

        for key, msg in self.mbox.items():
            # cast to Message so static checkers know .get is available
            msg = cast(Message, msg)
            msg_id = msg.get('Message-ID')
            if not msg_id:
                continue

            references = msg.get('References', "").split()
            self.metadata_map[msg_id] = {
                'key': key,
                'subject': msg.get('Subject', ''),
                'date': get_email_date(msg),
                'in_reply_to': msg.get('In-Reply-To'),
                'references': references[-1] if references else None
            }
            metadata_count += 1

        log_processing_step(
            self.logger, 2,
            f"메타데이터 수집 완료: 총 {metadata_count}개의 고유 메시지"
        )

    def backup_mbox(self, mbox_path):
        """간단한 mbox 백업 유틸리티"""
        try:
            dst = f"{mbox_path}.bak"
            shutil.copy2(mbox_path, dst)
            log_file_operation(self.logger, 'mbox 백업', dst, success=True)
            return dst
        except Exception as e:
            log_file_operation(self.logger, 'mbox 백업',
                               mbox_path, success=False, error_msg=str(e))
            return None

    def load_mbox_as_threads(self, mbox_path):
        """새로운 프로세서: mbox를 스레드 목록으로 읽어들이는 어댑터"""
        # backup for safety
        self.backup_mbox(mbox_path)
        threads = process_mailbox(mbox_path)
        # rebuild metadata_map from threads for compatibility
        self.metadata_map = {}
        counter = 0
        for thread in threads:
            for msg in thread:
                msg = cast(Message, msg)
                msg_id = msg.get('Message-ID')
                if not msg_id:
                    continue
                # use incremental key since mailbox keys not available from process_mailbox
                self.metadata_map[msg_id] = {
                    'key': counter,
                    'subject': msg.get('Subject', ''),
                    'date': get_email_date(msg),
                    'in_reply_to': msg.get('In-Reply-To'),
                    'references': (msg.get('References', '').split()[-1] if msg.get('References') else None)
                }
                counter += 1
        log_processing_step(
            self.logger, 2, f"스레드 기반 메타데이터 수집 완료: 총 {len(self.metadata_map)}개의 메시지")
        # store a synthetic mbox-like mapping to allow existing get_message_content to work

        class _SimpleMBox(dict):
            def get_message(self, k):
                return self.get(k)

        simple = _SimpleMBox()
        for i, thread in enumerate(threads):
            for j, msg in enumerate(thread):
                simple[(i * 100000) + j] = msg

        self.mbox = simple

    def get_all_message_metadata(self):
        """모든 메시지의 메타데이터와 기본 정보를 가져옵니다."""
        messages_info = []
        for msg_id, meta in self.metadata_map.items():
            # mbox에서 전체 메시지 가져오기
            if self.mbox and meta['key'] in self.mbox:
                full_msg = self.mbox[meta['key']]

                # 발신자, 수신자 정보 추출
                sender = decode_text(full_msg.get('From', ''))
                recipients = []
                for field in ['To', 'Cc', 'Bcc']:
                    if full_msg.get(field):
                        recipients.extend(
                            [addr.strip() for addr in decode_text(full_msg.get(field)).split(',')])

                # 첨부파일 정보 추출
                attachments = []
                total_size = 0

                if full_msg.is_multipart():
                    for part in full_msg.walk():
                        disposition = part.get('Content-Disposition', '')
                        if disposition and 'attachment' in disposition:
                            filename = part.get_filename()
                            if filename:
                                decoded_filename = decode_text(filename)
                                payload = part.get_payload(decode=True)
                                size = len(payload) if payload else 0
                                total_size += size

                                attachments.append({
                                    'filename': decoded_filename,
                                    'size': size,
                                    'content_type': part.get_content_type()
                                })

                messages_info.append({
                    'id': msg_id,
                    'key': meta['key'],
                    'subject': decode_text(meta['subject']),
                    'date': meta['date'],
                    'sender': sender,
                    'recipients': recipients,
                    'attachments': attachments,
                    'size': total_size
                })
            else:
                # mbox가 없거나 메시지를 찾을 수 없는 경우 기본 정보만
                messages_info.append({
                    'id': msg_id,
                    'key': meta['key'],
                    'subject': decode_text(meta['subject']),
                    'date': meta['date'],
                    'sender': '',
                    'recipients': [],
                    'attachments': [],
                    'size': 0
                })

        messages_info.sort(
            key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
        return messages_info

    def get_message_content(self, msg_id):
        """메시지의 상세 내용을 가져옵니다."""
        if msg_id not in self.metadata_map:
            return None

        meta = self.metadata_map[msg_id]
        if not self.mbox or meta['key'] not in self.mbox:
            return None

        full_msg = self.mbox[meta['key']]

        content = {
            'text': '',
            'html': '',
            'attachments': []
        }

        if full_msg.is_multipart():
            for part in full_msg.walk():
                disposition = part.get('Content-Disposition', '')
                content_type = part.get_content_type()

                if not disposition or 'attachment' not in disposition:
                    if content_type == 'text/plain' and not content['text']:
                        try:
                            text_payload = part.get_payload(decode=True)
                            if text_payload:
                                content['text'] = text_payload.decode(
                                    'utf-8', errors='ignore')
                        except Exception:
                            pass
                    elif content_type == 'text/html' and not content['html']:
                        try:
                            html_payload = part.get_payload(decode=True)
                            if html_payload:
                                content['html'] = html_payload.decode(
                                    'utf-8', errors='ignore')
                        except Exception:
                            pass
                elif disposition and 'attachment' in disposition:
                    filename = part.get_filename()
                    if filename:
                        decoded_filename = decode_text(filename)
                        payload = part.get_payload(decode=True)
                        content['attachments'].append({
                            'filename': decoded_filename,
                            'size': len(payload) if payload else 0,
                            'content_type': part.get_content_type()
                        })
        else:
            # 단일 파트 메시지
            content_type = full_msg.get_content_type()
            payload = full_msg.get_payload(decode=True)

            if payload:
                try:
                    text = payload.decode('utf-8', errors='ignore')
                    if content_type == 'text/html':
                        content['html'] = text
                    else:
                        content['text'] = text
                except Exception:
                    pass

        return content

    def process_single_message(self, msg_id, output_base_dir):
        if msg_id not in self.metadata_map:
            print(f"오류: 메시지 ID '{msg_id}'를 메타데이터 맵에서 찾을 수 없습니다.")
            return None  # HTML 파일 경로를 반환하지 않음

        meta = self.metadata_map[msg_id]
        full_msg = self.mbox.get_message(meta['key'])

        if not full_msg:
            print(f"  - 경고: Key '{meta['key']}'에 해당하는 전체 메시지를 찾을 수 없습니다.")
            return None

        is_excluded, reason = self._is_excluded(full_msg)
        if is_excluded:
            thread_folder_name = sanitize_filename(
                f"[{meta['date'].strftime('%Y-%m-%d')}] {decode_text(meta['subject'])}")
            thread_path = os.path.join(output_base_dir, thread_folder_name)
            excluded_dir = os.path.join(thread_path, 'excluded')
            os.makedirs(excluded_dir, exist_ok=True)
            base_filename = sanitize_filename(
                f"01_{decode_text(meta['subject'])}")
            excluded_filepath = os.path.join(
                excluded_dir, f"{base_filename}.eml")
            with open(excluded_filepath, 'wb') as f:
                f.write(full_msg.as_bytes())
            print(
                f" - [제외됨] {base_filename} (사유: {reason}). 'excluded' 폴더에 저장됨.")
            return None

        subject = decode_text(meta['subject'])
        base_filename = sanitize_filename(f"01_{subject}")

        thread_folder_name = sanitize_filename(
            f"[{meta['date'].strftime('%Y-%m-%d')}] {subject}")
        thread_path = os.path.join(output_base_dir, thread_folder_name)
        os.makedirs(thread_path, exist_ok=True)
        print(f"\n[메시지 처리 시작] '{thread_folder_name}'")

        html_body = None
        html_part = None
        cid_map = {}
        attachments = []

        for part in full_msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            disposition = part.get('Content-Disposition', '')
            content_id = part.get('Content-ID')

            if not html_part and part.get_content_type() == 'text/html' and 'attachment' not in disposition:
                html_part = part
            elif content_id and ('inline' in disposition or not disposition):
                cid = content_id.strip('<>')
                cid_map[cid] = part
            elif 'attachment' in disposition:
                attachments.append(part)

        if html_part:
            charset = html_part.get_content_charset() or 'utf-8'
            try:
                html_body = html_part.get_payload(
                    decode=True).decode(charset, errors='ignore')
            except (UnicodeDecodeError, LookupError):
                html_body = html_part.get_payload(
                    decode=True).decode('cp949', errors='ignore')

            for cid, image_part in cid_map.items():
                image_data = image_part.get_payload(decode=True)
                mime_type = image_part.get_content_type()
                base64_data = base64.b64encode(image_data).decode('utf-8')

                data_uri = f"data:{mime_type};base64,{base64_data}"
                html_body = html_body.replace(
                    f'src="cid:{cid}"', f'src="{data_uri}"')
                html_body = html_body.replace(
                    f"src='cid:{cid}'", f"src='{data_uri}'")

            html_filepath = os.path.join(thread_path, f"{base_filename}.html")
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_body)
            print(f"  - HTML 저장 (이미지 내장): {html_filepath}")
            return html_filepath  # HTML 파일 경로 반환

        for part in attachments:
            filename = part.get_filename()
            if filename:
                decoded_filename = decode_text(filename)
                sanitized_filename = sanitize_filename(decoded_filename)
                if sanitized_filename:
                    filepath = os.path.join(thread_path, sanitized_filename)
                    if not os.path.exists(filepath):
                        payload = part.get_payload(decode=True)
                        if payload:
                            with open(filepath, 'wb') as f:
                                f.write(payload)
                            print(f"  - 첨부파일 저장: {filepath}")
                        else:
                            print(
                                f"  - 경고: 첨부파일 '{sanitized_filename}'의 내용이 비어있습니다.")
        return None

    def convert_html_to_pdf(self, html_filepath, party, evidence_number_counter):
        # HTML 파일을 읽고 PDF로 변환하는 별도의 메서드
        try:
            with open(html_filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 증거번호 부여
            evidence_number_counter[party] = evidence_number_counter.get(
                party, 0) + 1
            evidence_number = f"{party} 제{evidence_number_counter[party]}호증"

            pdf_output_dir = os.path.join(
                os.path.dirname(html_filepath), 'pdf_evidence')
            os.makedirs(pdf_output_dir, exist_ok=True)
            pdf_filepath = os.path.join(pdf_output_dir, os.path.basename(
                html_filepath).replace('.html', '.pdf'))

            self.formatter.to_pdf(html_content, pdf_filepath, evidence_number)
            print(f"  - PDF 변환 및 증거번호 부여 완료: {pdf_filepath}")
            return True
        except Exception as e:
            print(f"  - PDF 변환 중 오류 발생 ({html_filepath}): {e}")
            return False

    def _is_excluded(self, msg):
        """
        향상된 메일 제외 로직
        """
        exclude_keywords = self.config.get('exclude_keywords', [])
        exclude_senders = self.config.get('exclude_senders', [])
        exclude_domains = self.config.get('exclude_domains', [])
        date_range_config = self.config.get('date_range', {})
        required_keywords_config = self.config.get('required_keywords', {})

        # required_keywords가 dict인지 확인하고 keywords 배열 추출
        if isinstance(required_keywords_config, dict):
            required_keywords = required_keywords_config.get('keywords', [])
        else:
            required_keywords = required_keywords_config or []

        start_date_str = date_range_config.get('start')
        end_date_str = date_range_config.get('end')
        start_date = datetime.strptime(
            start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(
            end_date_str, '%Y-%m-%d').date() if end_date_str else None

        subject = decode_text(msg.get('Subject', ''))

        # 메일 본문 추출
        body = ""
        for part in msg.walk():
            if part.get_content_maintype() == 'text':
                charset = part.get_content_charset() or 'utf-8'
                try:
                    body += part.get_payload(decode=True).decode(charset,
                                                                 errors='ignore')
                except (UnicodeDecodeError, LookupError):
                    body += part.get_payload(decode=True).decode('cp949',
                                                                 errors='ignore')

        full_content = subject + " " + body
        sender = msg.get('From', '')
        sender_email_match = re.search(r'<(.+?)>', sender)
        sender_email = sender_email_match.group(
            1) if sender_email_match else sender

        # 1. 제외 키워드 검사
        for keyword in exclude_keywords:
            if keyword.lower() in full_content.lower():
                return True, f"제외 키워드 '{keyword}' 포함"

        # 2. 제외 발신자 검사
        for ex_sender in exclude_senders:
            if ex_sender.lower() in sender_email.lower():
                return True, f"제외 발신자 '{ex_sender}' 포함"

        # 3. 제외 도메인 검사
        for domain in exclude_domains:
            if domain.lower() in sender_email.lower():
                return True, f"제외 도메인 '{domain}' 포함"

        # 4. 날짜 범위 검사
        email_date = get_email_date(msg)
        if email_date:
            email_date_only = email_date.date()
            if start_date and email_date_only < start_date:
                return True, f"시작일 '{start_date_str}' 이전"
            if end_date and email_date_only > end_date:
                return True, f"종료일 '{end_date_str}' 이후"

        # 5. 필수 키워드 검사 (키워드가 설정된 경우만)
        if required_keywords:  # 빈 배열이 아닌 경우에만 검사
            found_required = False
            for req_keyword in required_keywords:
                if req_keyword.lower() in full_content.lower():
                    found_required = True
                    break

            if not found_required:
                return True, f"필수 키워드 미포함 (요구: {', '.join(required_keywords[:3])}...)"

        return False, "포함"

    def process_mbox_with_streaming(self, mbox_path: str, party: str, output_dir: str = None) -> dict:
        """스트리밍을 지원하는 mbox 파일 처리"""
        # 포렌식 무결성 기록 시작
        if self.config.get('forensic_settings', {}).get('enable_chain_of_custody', False):
            custody_record = self.forensic_service.create_chain_of_custody(
                mbox_path,
                f"법정 증거 처리 시작: {party} 관련"
            )
            self.logger.info(
                f"연계보관성 기록 생성: {custody_record.original_hash[:16]}...")

        try:
            processed_count = 0
            evidence_files = []

            # 스트리밍 처리
            for message in self.streaming_processor.stream_emails(mbox_path):
                if self._should_include_email_streaming(message):
                    evidence_number = self.get_evidence_number(party)
                    evidence_data = self.process_email_to_evidence(
                        message, evidence_number)

                    if evidence_data:
                        evidence_files.append(evidence_data)
                        processed_count += 1

                # 통계 로그
                if processed_count > 0 and processed_count % self.config.get('performance_monitoring', {}).get('stats_interval_emails', 1000) == 0:
                    stats = self.streaming_processor.get_processing_statistics()
                    self.logger.info(f"처리 통계: {stats}")

            # 포렌식 보고서 생성
            if self.config.get('forensic_settings', {}).get('export_custody_log', False):
                custody_log_path = self.forensic_service.export_custody_log()
                self.logger.info(f"연계보관성 로그 저장: {custody_log_path}")

            return {
                'processed_emails': processed_count,
                'evidence_files': evidence_files,
                'mode': 'streaming' if self.streaming_processor.should_use_streaming(mbox_path) else 'normal',
                'processing_stats': self.streaming_processor.get_processing_statistics(),
                'custody_summary': self.forensic_service.get_custody_summary()
            }

        except Exception as e:
            self.logger.error(f"스트리밍 처리 중 오류: {str(e)}")
            raise

    def _should_include_email_streaming(self, message) -> bool:
        """스트리밍 처리용 이메일 포함 여부 판단"""
        try:
            subject = decode_text(message.get('Subject', ''))
            sender = decode_text(message.get('From', ''))

            # 기존 필터링 로직 재사용
            should_exclude, reason = self.should_exclude_email(
                subject, sender, "")
            return not should_exclude

        except Exception as e:
            self.logger.error(f"이메일 필터링 중 오류: {str(e)}")
            return False

    def get_evidence_number(self, prefix='갑'):
        """증거 번호 생성 (EvidenceGenerator 위임)"""
        return self.evidence_generator.get_evidence_number(prefix)

    def get_full_message_by_id(self, message_id):
        """메시지 ID로 전체 메시지 가져오기 (EvidenceGenerator 위임)"""
        return self.evidence_generator.get_full_message_by_id(message_id)

    def process_email_to_evidence(self, msg, evidence_number, extract_attachments=True):
        """이메일을 법정 증거로 처리 (EvidenceGenerator 위임)"""
        return self.evidence_generator.process_email_to_evidence(
            msg, evidence_number, extract_attachments
        )
