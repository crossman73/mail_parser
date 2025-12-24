"""
Evidence data model for court submission.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class EvidenceType(Enum):
    """증거 유형"""
    GAP = "갑"  # 신청인 증거
    EUL = "을"  # 피신청인 증거


class EvidenceStatus(Enum):
    """증거 처리 상태"""
    PENDING = "pending"      # 대기중
    PROCESSING = "processing"  # 처리중
    COMPLETED = "completed"   # 완료
    ERROR = "error"          # 오류


@dataclass
class EvidenceModel:
    """법정 증거 데이터 모델"""

    # 증거 식별 정보
    evidence_id: str
    evidence_type: EvidenceType
    evidence_sequence: int

    # 관련 메일 정보
    email_message_id: str
    email_subject: str
    email_date: datetime

    # 증거 파일 정보
    original_file: Optional[Path] = None
    html_file: Optional[Path] = None
    pdf_file: Optional[Path] = None
    attachment_files: List[Path] = None

    # 처리 정보
    status: EvidenceStatus = EvidenceStatus.PENDING
    created_date: datetime = None
    processed_date: Optional[datetime] = None

    # 법정 제출 정보
    court_case_number: Optional[str] = None
    submission_date: Optional[datetime] = None

    # 무결성 정보
    original_hash: Optional[str] = None
    verification_hash: Optional[str] = None
    integrity_verified: bool = False

    # 메타데이터
    description: Optional[str] = None
    tags: List[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """초기화 후 처리"""
        if self.attachment_files is None:
            self.attachment_files = []
        if self.tags is None:
            self.tags = []
        if self.created_date is None:
            self.created_date = datetime.now()

    @property
    def evidence_label(self) -> str:
        """증거 라벨 반환 (예: 갑 제1호증)"""
        return f"{self.evidence_type.value} 제{self.evidence_sequence}호증"

    @property
    def evidence_number(self) -> str:
        """증거 번호 반환 (예: 갑1)"""
        return f"{self.evidence_type.value}{self.evidence_sequence}"

    @property
    def is_complete(self) -> bool:
        """증거가 완전한지 확인"""
        return (
            self.status == EvidenceStatus.COMPLETED and
            self.html_file and self.html_file.exists() and
            self.pdf_file and self.pdf_file.exists()
        )

    @property
    def has_attachments(self) -> bool:
        """첨부파일이 있는지 확인"""
        return len(self.attachment_files) > 0

    @property
    def attachment_count(self) -> int:
        """첨부파일 개수"""
        return len(self.attachment_files)

    def add_attachment(self, file_path: Path) -> None:
        """첨부파일 추가"""
        if file_path not in self.attachment_files:
            self.attachment_files.append(file_path)

    def remove_attachment(self, file_path: Path) -> None:
        """첨부파일 제거"""
        if file_path in self.attachment_files:
            self.attachment_files.remove(file_path)

    def mark_completed(self) -> None:
        """처리 완료로 표시"""
        self.status = EvidenceStatus.COMPLETED
        self.processed_date = datetime.now()

    def mark_error(self) -> None:
        """오류로 표시"""
        self.status = EvidenceStatus.ERROR
        self.processed_date = datetime.now()

    def verify_integrity(self) -> bool:
        """무결성 검증"""
        if not self.original_hash or not self.verification_hash:
            return False

        self.integrity_verified = self.original_hash == self.verification_hash
        return self.integrity_verified

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'evidence_sequence': self.evidence_sequence,
            'email_message_id': self.email_message_id,
            'email_subject': self.email_subject,
            'email_date': self.email_date.isoformat(),
            'original_file': str(self.original_file) if self.original_file else None,
            'html_file': str(self.html_file) if self.html_file else None,
            'pdf_file': str(self.pdf_file) if self.pdf_file else None,
            'attachment_files': [str(f) for f in self.attachment_files],
            'status': self.status.value,
            'created_date': self.created_date.isoformat(),
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'court_case_number': self.court_case_number,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'original_hash': self.original_hash,
            'verification_hash': self.verification_hash,
            'integrity_verified': self.integrity_verified,
            'description': self.description,
            'tags': self.tags,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceModel':
        """딕셔너리에서 생성"""
        # 날짜 변환
        email_date = datetime.fromisoformat(data['email_date'])
        created_date = datetime.fromisoformat(data['created_date'])
        processed_date = None
        if data.get('processed_date'):
            processed_date = datetime.fromisoformat(data['processed_date'])
        submission_date = None
        if data.get('submission_date'):
            submission_date = datetime.fromisoformat(data['submission_date'])

        # 경로 변환
        original_file = Path(data['original_file']) if data.get(
            'original_file') else None
        html_file = Path(data['html_file']) if data.get('html_file') else None
        pdf_file = Path(data['pdf_file']) if data.get('pdf_file') else None
        attachment_files = [Path(f) for f in data.get('attachment_files', [])]

        return cls(
            evidence_id=data['evidence_id'],
            evidence_type=EvidenceType(data['evidence_type']),
            evidence_sequence=data['evidence_sequence'],
            email_message_id=data['email_message_id'],
            email_subject=data['email_subject'],
            email_date=email_date,
            original_file=original_file,
            html_file=html_file,
            pdf_file=pdf_file,
            attachment_files=attachment_files,
            status=EvidenceStatus(data['status']),
            created_date=created_date,
            processed_date=processed_date,
            court_case_number=data.get('court_case_number'),
            submission_date=submission_date,
            original_hash=data.get('original_hash'),
            verification_hash=data.get('verification_hash'),
            integrity_verified=data.get('integrity_verified', False),
            description=data.get('description'),
            tags=data.get('tags', []),
            notes=data.get('notes')
        )
