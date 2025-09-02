"""
EmailEvidenceProcessor의 확장 메서드들
실제 증거 생성 및 처리를 위한 추가 기능
"""

import hashlib
import json
import os
from datetime import datetime
from email.utils import parseaddr
from pathlib import Path


class EvidenceGenerator:
    """증거 생성 및 관리 클래스"""

    def __init__(self, processor):
        self.processor = processor
        self.evidence_counters = {}
        self.output_dir = Path('processed_emails')
        self.output_dir.mkdir(exist_ok=True)

    def get_evidence_number(self, prefix='갑'):
        """증거 번호 생성"""
        if prefix not in self.evidence_counters:
            self.evidence_counters[prefix] = 0

        self.evidence_counters[prefix] += 1
        return f"{prefix} 제{self.evidence_counters[prefix]}호증"

    def get_full_message_by_id(self, message_id):
        """메시지 ID로 전체 메시지 가져오기"""
        if not self.processor.mbox:
            return None

        for key, msg in self.processor.mbox.items():
            if msg.get('Message-ID') == message_id:
                return msg
        return None

    def process_email_to_evidence(self, msg, evidence_number, extract_attachments=True):
        """이메일을 법정 증거로 처리"""
        try:
            # 기본 메타데이터 추출
            subject = msg.get('Subject', '제목 없음')
            sender = msg.get('From', '')
            recipients = msg.get('To', '')
            date_sent = msg.get('Date', '')
            message_id = msg.get('Message-ID', '')

            # 안전한 폴더명 생성
            safe_subject = self._sanitize_filename(subject)
            folder_name = f"[{datetime.now().strftime('%Y-%m-%d')}]_{safe_subject}"

            evidence_dir = self.output_dir / folder_name
            evidence_dir.mkdir(exist_ok=True)

            # 이메일 헤더 정보 저장
            headers_info = {
                'evidence_number': evidence_number,
                'subject': subject,
                'from': sender,
                'to': recipients,
                'date': date_sent,
                'message_id': message_id,
                'generated_at': datetime.now().isoformat(),
                'integrity_hash': ''
            }

            # 본문 추출 및 저장
            body_text = self._extract_email_body(msg)

            # 첨부파일 처리
            attachments = []
            if extract_attachments and msg.is_multipart():
                attachments = self._extract_attachments(msg, evidence_dir)

            # HTML 증거 문서 생성
            html_content = self._generate_evidence_html(
                headers_info, body_text, attachments
            )

            html_file = evidence_dir / \
                f"{evidence_number.replace(' ', '_')}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # PDF 증거 문서 생성
            pdf_file = evidence_dir / \
                f"{evidence_number.replace(' ', '_')}.pdf"
            self._generate_evidence_pdf(
                html_content, pdf_file, evidence_number)

            # 무결성 해시 생성
            integrity_hash = self._calculate_integrity_hash(
                html_file, pdf_file, attachments)
            headers_info['integrity_hash'] = integrity_hash

            # 메타데이터 저장
            metadata_file = evidence_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(headers_info, f, ensure_ascii=False, indent=2)

            return {
                'evidence_number': evidence_number,
                'subject': subject,
                'folder_path': str(evidence_dir),
                'html_file': str(html_file),
                'pdf_file': str(pdf_file),
                'attachments_count': len(attachments),
                'integrity_hash': integrity_hash,
                'generated_at': headers_info['generated_at']
            }

        except Exception as e:
            self.processor.logger.error(f"증거 생성 실패: {str(e)}")
            raise

    def _sanitize_filename(self, filename):
        """파일명 안전화"""
        import re

        # 윈도우 파일명 금지 문자 제거
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 길이 제한 (50자)
        if len(filename) > 50:
            filename = filename[:47] + '...'
        return filename

    def _extract_email_body(self, msg):
        """이메일 본문 추출"""
        body_parts = []

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        content = part.get_payload(decode=True)
                        body_parts.append(content.decode(
                            charset, errors='ignore'))
                    except:
                        body_parts.append("(본문 디코딩 실패)")
                elif part.get_content_type() == 'text/html':
                    # HTML 본문도 저장 (나중에 사용할 수 있음)
                    pass
        else:
            charset = msg.get_content_charset() or 'utf-8'
            try:
                content = msg.get_payload(decode=True)
                body_parts.append(content.decode(charset, errors='ignore'))
            except:
                body_parts.append("(본문 디코딩 실패)")

        return '\n\n'.join(body_parts)

    def _extract_attachments(self, msg, evidence_dir):
        """첨부파일 추출"""
        attachments = []
        attachment_dir = evidence_dir / 'attachments'

        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    attachment_dir.mkdir(exist_ok=True)

                    # 안전한 파일명 생성
                    safe_filename = self._sanitize_filename(filename)
                    attachment_path = attachment_dir / safe_filename

                    try:
                        with open(attachment_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))

                        attachments.append({
                            'filename': filename,
                            'safe_filename': safe_filename,
                            'path': str(attachment_path),
                            'size': os.path.getsize(attachment_path)
                        })
                    except Exception as e:
                        self.processor.logger.warning(
                            f"첨부파일 추출 실패 {filename}: {str(e)}")

        return attachments

    def _generate_evidence_html(self, headers, body, attachments):
        """HTML 증거 문서 생성"""
        html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>법정 증거 - {headers['evidence_number']}</title>
    <style>
        body {{ font-family: '맑은 고딕', 'Malgun Gothic', Arial, sans-serif; margin: 20px; }}
        .header {{ border: 2px solid #000; padding: 20px; margin-bottom: 20px; }}
        .evidence-number {{ font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; }}
        .metadata {{ margin-bottom: 20px; }}
        .metadata table {{ width: 100%; border-collapse: collapse; }}
        .metadata th, .metadata td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        .metadata th {{ background-color: #f5f5f5; font-weight: bold; }}
        .body-content {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .attachments {{ margin: 20px 0; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        .integrity {{ background-color: #f0f8ff; padding: 10px; margin: 10px 0; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="evidence-number">{headers['evidence_number']}</div>
        <div class="metadata">
            <table>
                <tr><th>제목</th><td>{headers['subject']}</td></tr>
                <tr><th>발신자</th><td>{headers['from']}</td></tr>
                <tr><th>수신자</th><td>{headers['to']}</td></tr>
                <tr><th>발송일시</th><td>{headers['date']}</td></tr>
                <tr><th>메시지 ID</th><td>{headers['message_id']}</td></tr>
                <tr><th>증거 생성일</th><td>{headers['generated_at']}</td></tr>
            </table>
        </div>
    </div>

    <div class="body-content">
        <h3>이메일 본문</h3>
        <pre style="white-space: pre-wrap; word-wrap: break-word;">{body}</pre>
    </div>

    {self._generate_attachments_html(attachments)}

    <div class="footer">
        <div class="integrity">
            <strong>무결성 검증 해시:</strong> {headers.get('integrity_hash', '생성 중...')}
        </div>
        <p>본 문서는 법정 제출용 이메일 증거로 자동 생성되었습니다.</p>
        <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
    </div>
</body>
</html>"""
        return html_template

    def _generate_attachments_html(self, attachments):
        """첨부파일 HTML 섹션 생성"""
        if not attachments:
            return ""

        html = '<div class="attachments"><h3>첨부파일 목록</h3><table border="1"><tr><th>파일명</th><th>크기</th><th>경로</th></tr>'

        for att in attachments:
            size_mb = att['size'] / (1024 * 1024)
            html += f"<tr><td>{att['filename']}</td><td>{size_mb:.2f} MB</td><td>{att['path']}</td></tr>"

        html += '</table></div>'
        return html

    def _generate_evidence_pdf(self, html_content, pdf_path, evidence_number):
        """PDF 증거 문서 생성"""
        try:
            # PDF 생성 로직 (간단한 구현)
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(str(pdf_path), pagesize=A4)

            # 간단한 PDF 헤더 작성
            c.drawString(100, 750, f"법정 증거: {evidence_number}")
            c.drawString(
                100, 720, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(100, 690, "본 PDF는 이메일 증거의 요약본입니다.")
            c.drawString(100, 660, "상세 내용은 HTML 파일을 참조하시기 바랍니다.")

            c.save()

        except Exception as e:
            self.processor.logger.warning(f"PDF 생성 실패: {str(e)}")

    def _calculate_integrity_hash(self, html_file, pdf_file, attachments):
        """무결성 해시 계산"""
        hash_obj = hashlib.sha256()

        # HTML 파일 해시
        if os.path.exists(html_file):
            with open(html_file, 'rb') as f:
                hash_obj.update(f.read())

        # PDF 파일 해시 (존재하는 경우)
        if os.path.exists(pdf_file):
            with open(pdf_file, 'rb') as f:
                hash_obj.update(f.read())

        # 첨부파일 해시
        for att in attachments:
            if os.path.exists(att['path']):
                with open(att['path'], 'rb') as f:
                    hash_obj.update(f.read())

        return hash_obj.hexdigest()
