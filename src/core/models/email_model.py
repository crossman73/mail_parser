"""
Email data model for the evidence processing system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class EmailModel:
    """메일 데이터 모델"""

    # 기본 메일 정보
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: datetime

    # 메일 내용
    body_text: Optional[str] = None
    body_html: Optional[str] = None

    # 첨부파일 정보
    attachments: List[str] = None
    attachment_count: int = 0

    # 법정 증거 정보
    evidence_number: Optional[str] = None
    evidence_type: str = "갑"  # 갑, 을
    evidence_sequence: Optional[int] = None

    # 처리 정보
    processed: bool = False
    processed_date: Optional[datetime] = None
    output_directory: Optional[Path] = None

    # 파일 경로
    html_path: Optional[Path] = None
    pdf_path: Optional[Path] = None

    # 메타데이터
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: List[str] = None

    # 무결성 검증
    original_hash: Optional[str] = None
    processed_hash: Optional[str] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.attachments is None:
            self.attachments = []
        if self.references is None:
            self.references = []

        self.attachment_count = len(self.attachments)

    @property
    def date_str(self) -> str:
        """날짜 문자열 반환"""
        return self.date.strftime("%Y-%m-%d")

    @property
    def evidence_label(self) -> str:
        """증거 라벨 반환 (예: 갑 제1호증)"""
        if self.evidence_sequence:
            return f"{self.evidence_type} 제{self.evidence_sequence}호증"
        return ""

    @property
    def safe_subject(self) -> str:
        """파일명에 안전한 제목 반환"""
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '_', self.subject)
        return safe[:50]  # 길이 제한

    @property
    def folder_name(self) -> str:
        """폴더명 반환"""
        return f"[{self.date_str}]_{self.safe_subject}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'message_id': self.message_id,
            'subject': self.subject,
            'sender': self.sender,
            'recipients': self.recipients,
            'date': self.date.isoformat(),
            'body_text': self.body_text,
            'body_html': self.body_html,
            'attachments': self.attachments,
            'attachment_count': self.attachment_count,
            'evidence_number': self.evidence_number,
            'evidence_type': self.evidence_type,
            'evidence_sequence': self.evidence_sequence,
            'processed': self.processed,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'output_directory': str(self.output_directory) if self.output_directory else None,
            'html_path': str(self.html_path) if self.html_path else None,
            'pdf_path': str(self.pdf_path) if self.pdf_path else None,
            'thread_id': self.thread_id,
            'in_reply_to': self.in_reply_to,
            'references': self.references,
            'original_hash': self.original_hash,
            'processed_hash': self.processed_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailModel':
        """딕셔너리에서 생성"""
        # 날짜 변환
        date = datetime.fromisoformat(data['date']) if isinstance(
            data['date'], str) else data['date']
        processed_date = None
        if data.get('processed_date'):
            processed_date = datetime.fromisoformat(data['processed_date'])

        # 경로 변환
        output_directory = Path(data['output_directory']) if data.get(
            'output_directory') else None
        html_path = Path(data['html_path']) if data.get('html_path') else None
        pdf_path = Path(data['pdf_path']) if data.get('pdf_path') else None

        return cls(
            message_id=data['message_id'],
            subject=data['subject'],
            sender=data['sender'],
            recipients=data['recipients'],
            date=date,
            body_text=data.get('body_text'),
            body_html=data.get('body_html'),
            attachments=data.get('attachments', []),
            attachment_count=data.get('attachment_count', 0),
            evidence_number=data.get('evidence_number'),
            evidence_type=data.get('evidence_type', '갑'),
            evidence_sequence=data.get('evidence_sequence'),
            processed=data.get('processed', False),
            processed_date=processed_date,
            output_directory=output_directory,
            html_path=html_path,
            pdf_path=pdf_path,
            thread_id=data.get('thread_id'),
            in_reply_to=data.get('in_reply_to'),
            references=data.get('references', []),
            original_hash=data.get('original_hash'),
            processed_hash=data.get('processed_hash')
        )
