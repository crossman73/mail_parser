"""
Evidence management service for court submission.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models import EmailModel, EvidenceModel, EvidenceType, EvidenceStatus
from .integrity_service import IntegrityService


class EvidenceManager:
    """법정 증거 관리 서비스"""

    def __init__(self, output_dir: str = "processed_emails"):
        """초기화"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.integrity_service = IntegrityService()
        self.evidence_list: List[EvidenceModel] = []
        self.evidence_counter = {"갑": 0, "을": 0}

        # 메타데이터 파일 경로
        self.metadata_file = self.output_dir / "evidence_metadata.json"

        # 기존 증거 목록 로드
        self._load_existing_evidence()

    def _load_existing_evidence(self):
        """기존 증거 목록 로드"""
        if not self.metadata_file.exists():
            return

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for evidence_data in data.get('evidence_list', []):
                evidence = EvidenceModel.from_dict(evidence_data)
                self.evidence_list.append(evidence)

            # 카운터 업데이트
            for evidence in self.evidence_list:
                evidence_type = evidence.evidence_type.value
                if evidence.evidence_sequence > self.evidence_counter[evidence_type]:
                    self.evidence_counter[evidence_type] = evidence.evidence_sequence

        except Exception as e:
            print(f"기존 증거 목록 로드 오류: {e}")

    def _save_metadata(self):
        """메타데이터 저장"""
        try:
            data = {
                'evidence_list': [evidence.to_dict() for evidence in self.evidence_list],
                'evidence_counter': self.evidence_counter,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"메타데이터 저장 오류: {e}")

    def create_evidence(
        self,
        email: EmailModel,
        evidence_type: EvidenceType = EvidenceType.GAP,
        court_case_number: Optional[str] = None
    ) -> EvidenceModel:
        """이메일로부터 법정 증거 생성"""

        # 증거 번호 생성
        self.evidence_counter[evidence_type.value] += 1
        evidence_sequence = self.evidence_counter[evidence_type.value]

        # 증거 ID 생성
        evidence_id = f"{evidence_type.value}_{evidence_sequence}_{uuid.uuid4().hex[:8]}"

        # 증거 모델 생성
        evidence = EvidenceModel(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            evidence_sequence=evidence_sequence,
            email_message_id=email.message_id,
            email_subject=email.subject,
            email_date=email.date,
            court_case_number=court_case_number,
            status=EvidenceStatus.PENDING
        )

        # 증거 리스트에 추가
        self.evidence_list.append(evidence)

        # 메타데이터 저장
        self._save_metadata()

        return evidence

    def process_evidence(self, evidence: EvidenceModel, email: EmailModel) -> bool:
        """증거 처리 (HTML, PDF 생성)"""
        try:
            evidence.status = EvidenceStatus.PROCESSING

            # 출력 디렉터리 생성
            folder_name = f"[{email.date_str}]_{email.safe_subject}"
            evidence_dir = self.output_dir / folder_name
            evidence_dir.mkdir(exist_ok=True)

            # HTML 파일 생성
            html_filename = f"{evidence.evidence_number}_{email.safe_subject}.html"
            html_path = evidence_dir / html_filename

            html_content = self._generate_html_content(email, evidence)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            evidence.html_file = html_path

            # PDF 파일 생성
            pdf_filename = f"{evidence.evidence_number}_{email.safe_subject}.pdf"
            pdf_path = evidence_dir / pdf_filename

            if self._generate_pdf_from_html(html_path, pdf_path):
                evidence.pdf_file = pdf_path

            # 무결성 검증
            evidence.original_hash = email.original_hash
            evidence.verification_hash = self.integrity_service.calculate_file_hash(
                str(html_path))
            evidence.verify_integrity()

            # 완료 처리
            evidence.mark_completed()

            # 이메일 모델 업데이트
            email.evidence_number = evidence.evidence_number
            email.evidence_sequence = evidence.evidence_sequence
            email.processed = True
            email.processed_date = datetime.now()
            email.output_directory = evidence_dir
            email.html_path = html_path
            email.pdf_path = pdf_path

            # 메타데이터 저장
            self._save_metadata()

            return True

        except Exception as e:
            print(f"증거 처리 오류 ({evidence.evidence_id}): {e}")
            evidence.mark_error()
            self._save_metadata()
            return False

    def _generate_html_content(self, email: EmailModel, evidence: EvidenceModel) -> str:
        """HTML 콘텐츠 생성"""

        # 기본 HTML 템플릿
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{evidence_label} - {subject}</title>
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 20px; }}
                .header {{ border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
                .evidence-label {{ font-size: 24px; font-weight: bold; color: #d63031; }}
                .email-info {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin-bottom: 20px; }}
                .email-info table {{ width: 100%; border-collapse: collapse; }}
                .email-info td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
                .email-info td:first-child {{ font-weight: bold; width: 100px; }}
                .content {{ line-height: 1.6; }}
                .attachments {{ margin-top: 20px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="evidence-label">{evidence_label}</div>
            </div>

            <div class="email-info">
                <table>
                    <tr><td>제목</td><td>{subject}</td></tr>
                    <tr><td>발신자</td><td>{sender}</td></tr>
                    <tr><td>수신자</td><td>{recipients}</td></tr>
                    <tr><td>날짜</td><td>{date}</td></tr>
                    <tr><td>메시지ID</td><td>{message_id}</td></tr>
                    {attachment_info}
                </table>
            </div>

            <div class="content">
                <h3>메일 내용</h3>
                {body_content}
            </div>

            {attachments_section}

            <div class="footer">
                <p>증거 생성일: {created_date}</p>
                <p>무결성 해시: {hash_value}</p>
            </div>
        </body>
        </html>
        """

        # 데이터 준비
        recipients_str = '; '.join(
            email.recipients) if email.recipients else '없음'

        attachment_info = ""
        if email.attachment_count > 0:
            attachment_info = f"<tr><td>첨부파일</td><td>{email.attachment_count}개</td></tr>"

        # 본문 내용 처리
        body_content = ""
        if email.body_html:
            # HTML 본문이 있는 경우
            body_content = email.body_html
        elif email.body_text:
            # 텍스트 본문을 HTML로 변환
            import html
            escaped_text = html.escape(email.body_text)
            body_content = f"<pre>{escaped_text}</pre>"
        else:
            body_content = "<p><em>본문 내용이 없습니다.</em></p>"

        # 첨부파일 섹션
        attachments_section = ""
        if email.attachments:
            attachments_list = "<ul>"
            for attachment in email.attachments:
                attachments_list += f"<li>{attachment}</li>"
            attachments_list += "</ul>"

            attachments_section = f"""
            <div class="attachments">
                <h3>첨부파일</h3>
                {attachments_list}
            </div>
            """

        # HTML 생성
        return html_template.format(
            evidence_label=evidence.evidence_label,
            subject=email.subject,
            sender=email.sender,
            recipients=recipients_str,
            date=email.date.strftime("%Y년 %m월 %d일 %H:%M:%S"),
            message_id=email.message_id,
            attachment_info=attachment_info,
            body_content=body_content,
            attachments_section=attachments_section,
            created_date=datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S"),
            hash_value=email.original_hash[:16] +
            "..." if email.original_hash else "N/A"
        )

    def _generate_pdf_from_html(self, html_path: Path, pdf_path: Path) -> bool:
        """HTML에서 PDF 생성"""
        try:
            # 여기서는 간단한 구현만 제공
            # 실제로는 reportlab이나 weasyprint 등을 사용
            print(f"PDF 생성: {html_path} -> {pdf_path}")
            # 임시로 빈 PDF 파일 생성
            pdf_path.touch()
            return True
        except Exception as e:
            print(f"PDF 생성 오류: {e}")
            return False

    def get_evidence_by_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        """ID로 증거 조회"""
        for evidence in self.evidence_list:
            if evidence.evidence_id == evidence_id:
                return evidence
        return None

    def get_evidence_by_sequence(self, evidence_type: EvidenceType, sequence: int) -> Optional[EvidenceModel]:
        """증거 유형과 순번으로 조회"""
        for evidence in self.evidence_list:
            if evidence.evidence_type == evidence_type and evidence.evidence_sequence == sequence:
                return evidence
        return None

    def get_evidence_list(
        self,
        evidence_type: Optional[EvidenceType] = None,
        status: Optional[EvidenceStatus] = None
    ) -> List[EvidenceModel]:
        """증거 목록 조회"""
        filtered = self.evidence_list

        if evidence_type:
            filtered = [
                e for e in filtered if e.evidence_type == evidence_type]

        if status:
            filtered = [e for e in filtered if e.status == status]

        return sorted(filtered, key=lambda x: (x.evidence_type.value, x.evidence_sequence))

    def get_evidence_statistics(self) -> Dict[str, Any]:
        """증거 통계 정보"""
        total_count = len(self.evidence_list)
        gap_count = len(
            [e for e in self.evidence_list if e.evidence_type == EvidenceType.GAP])
        eul_count = len(
            [e for e in self.evidence_list if e.evidence_type == EvidenceType.EUL])

        completed_count = len(
            [e for e in self.evidence_list if e.status == EvidenceStatus.COMPLETED])
        pending_count = len(
            [e for e in self.evidence_list if e.status == EvidenceStatus.PENDING])
        error_count = len(
            [e for e in self.evidence_list if e.status == EvidenceStatus.ERROR])

        return {
            'total_count': total_count,
            'by_type': {
                'gap': gap_count,
                'eul': eul_count
            },
            'by_status': {
                'completed': completed_count,
                'pending': pending_count,
                'error': error_count
            },
            'completion_rate': completed_count / total_count * 100 if total_count > 0 else 0
        }

    def delete_evidence(self, evidence_id: str) -> bool:
        """증거 삭제"""
        evidence = self.get_evidence_by_id(evidence_id)
        if not evidence:
            return False

        try:
            # 파일 삭제
            if evidence.html_file and evidence.html_file.exists():
                evidence.html_file.unlink()
            if evidence.pdf_file and evidence.pdf_file.exists():
                evidence.pdf_file.unlink()

            # 목록에서 제거
            self.evidence_list.remove(evidence)

            # 메타데이터 저장
            self._save_metadata()

            return True

        except Exception as e:
            print(f"증거 삭제 오류 ({evidence_id}): {e}")
            return False
