"""
Attachment data model for email evidence system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum
import mimetypes


class AttachmentType(Enum):
    """첨부파일 유형"""
    DOCUMENT = "document"    # 문서 (PDF, DOC, etc.)
    IMAGE = "image"          # 이미지 (JPG, PNG, etc.)
    SPREADSHEET = "spreadsheet"  # 스프레드시트 (XLS, etc.)
    ARCHIVE = "archive"      # 압축파일 (ZIP, RAR, etc.)
    EMAIL = "email"          # 이메일 파일 (EML, MSG, etc.)
    OTHER = "other"          # 기타


@dataclass
class AttachmentModel:
    """첨부파일 데이터 모델"""

    # 기본 정보
    attachment_id: str
    filename: str
    original_filename: str
    file_path: Path

    # 파일 속성
    file_size: int  # bytes
    mime_type: str
    attachment_type: AttachmentType

    # 메일 관련 정보
    email_message_id: str
    email_subject: str

    # 처리 정보
    extracted_date: datetime
    is_inline: bool = False
    content_id: Optional[str] = None

    # 무결성 정보
    file_hash: Optional[str] = None
    verified: bool = False

    # 변환 정보
    converted_pdf: Optional[Path] = None
    thumbnail_path: Optional[Path] = None

    # 메타데이터
    description: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def create_from_file(
        cls,
        attachment_id: str,
        file_path: Path,
        email_message_id: str,
        email_subject: str,
        original_filename: Optional[str] = None,
        is_inline: bool = False,
        content_id: Optional[str] = None
    ) -> 'AttachmentModel':
        """파일에서 첨부파일 모델 생성"""

        if not file_path.exists():
            raise FileNotFoundError(f"Attachment file not found: {file_path}")

        filename = file_path.name
        if original_filename is None:
            original_filename = filename

        # 파일 크기
        file_size = file_path.stat().st_size

        # MIME 타입 추정
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # 첨부파일 유형 결정
        attachment_type = cls._determine_attachment_type(mime_type, filename)

        return cls(
            attachment_id=attachment_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            attachment_type=attachment_type,
            email_message_id=email_message_id,
            email_subject=email_subject,
            extracted_date=datetime.now(),
            is_inline=is_inline,
            content_id=content_id
        )

    @staticmethod
    def _determine_attachment_type(mime_type: str, filename: str) -> AttachmentType:
        """MIME 타입과 파일명으로 첨부파일 유형 결정"""

        # 이미지
        if mime_type.startswith('image/'):
            return AttachmentType.IMAGE

        # 문서
        if mime_type in [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            'application/rtf'
        ]:
            return AttachmentType.DOCUMENT

        # 스프레드시트
        if mime_type in [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ]:
            return AttachmentType.SPREADSHEET

        # 압축파일
        if mime_type in [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/gzip',
            'application/x-tar'
        ]:
            return AttachmentType.ARCHIVE

        # 이메일 파일
        if mime_type in ['message/rfc822'] or filename.lower().endswith(('.eml', '.msg')):
            return AttachmentType.EMAIL

        return AttachmentType.OTHER

    @property
    def file_size_mb(self) -> float:
        """파일 크기 (MB)"""
        return self.file_size / (1024 * 1024)

    @property
    def file_size_human(self) -> str:
        """사람이 읽기 쉬운 파일 크기"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def is_image(self) -> bool:
        """이미지 파일인지 확인"""
        return self.attachment_type == AttachmentType.IMAGE

    @property
    def is_document(self) -> bool:
        """문서 파일인지 확인"""
        return self.attachment_type == AttachmentType.DOCUMENT

    @property
    def file_extension(self) -> str:
        """파일 확장자"""
        return self.file_path.suffix.lower()

    def exists(self) -> bool:
        """파일이 존재하는지 확인"""
        return self.file_path.exists()

    def calculate_hash(self) -> str:
        """파일 해시 계산"""
        import hashlib

        if not self.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        hasher = hashlib.sha256()
        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        self.file_hash = hasher.hexdigest()
        return self.file_hash

    def verify_integrity(self) -> bool:
        """파일 무결성 검증"""
        if not self.file_hash:
            return False

        current_hash = self.calculate_hash()
        self.verified = (current_hash == self.file_hash)
        return self.verified

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'attachment_id': self.attachment_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': str(self.file_path),
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'attachment_type': self.attachment_type.value,
            'email_message_id': self.email_message_id,
            'email_subject': self.email_subject,
            'extracted_date': self.extracted_date.isoformat(),
            'is_inline': self.is_inline,
            'content_id': self.content_id,
            'file_hash': self.file_hash,
            'verified': self.verified,
            'converted_pdf': str(self.converted_pdf) if self.converted_pdf else None,
            'thumbnail_path': str(self.thumbnail_path) if self.thumbnail_path else None,
            'description': self.description,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttachmentModel':
        """딕셔너리에서 생성"""
        extracted_date = datetime.fromisoformat(data['extracted_date'])

        converted_pdf = None
        if data.get('converted_pdf'):
            converted_pdf = Path(data['converted_pdf'])

        thumbnail_path = None
        if data.get('thumbnail_path'):
            thumbnail_path = Path(data['thumbnail_path'])

        return cls(
            attachment_id=data['attachment_id'],
            filename=data['filename'],
            original_filename=data['original_filename'],
            file_path=Path(data['file_path']),
            file_size=data['file_size'],
            mime_type=data['mime_type'],
            attachment_type=AttachmentType(data['attachment_type']),
            email_message_id=data['email_message_id'],
            email_subject=data['email_subject'],
            extracted_date=extracted_date,
            is_inline=data.get('is_inline', False),
            content_id=data.get('content_id'),
            file_hash=data.get('file_hash'),
            verified=data.get('verified', False),
            converted_pdf=converted_pdf,
            thumbnail_path=thumbnail_path,
            description=data.get('description'),
            notes=data.get('notes')
        )
