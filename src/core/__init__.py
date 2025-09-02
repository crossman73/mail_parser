"""
Core email evidence processing system.
"""

# 모델
from .models import (
    EmailModel,
    EvidenceModel,
    EvidenceType,
    EvidenceStatus,
    TimelineModel,
    TimelineEvent,
    TimelineEventType,
    AttachmentModel,
    AttachmentType
)

# 서비스
from .services import (
    EmailProcessor,
    EvidenceManager,
    TimelineGenerator,
    IntegrityService
)

# 유틸리티
from .utils import (
    decode_text,
    sanitize_filename,
    get_email_date,
    format_korean_date,
    ensure_directory,
    safe_filename,
    calculate_file_hash,
    calculate_data_hash
)

__all__ = [
    # Models
    'EmailModel',
    'EvidenceModel',
    'EvidenceType',
    'EvidenceStatus',
    'TimelineModel',
    'TimelineEvent',
    'TimelineEventType',
    'AttachmentModel',
    'AttachmentType',

    # Services
    'EmailProcessor',
    'EvidenceManager',
    'TimelineGenerator',
    'IntegrityService',

    # Utils
    'decode_text',
    'sanitize_filename',
    'get_email_date',
    'format_korean_date',
    'ensure_directory',
    'safe_filename',
    'calculate_file_hash',
    'calculate_data_hash'
]
