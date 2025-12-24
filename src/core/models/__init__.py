"""
Core data models for the email evidence processing system.
"""

from .email_model import EmailModel
from .evidence_model import EvidenceModel, EvidenceType, EvidenceStatus
from .timeline_model import TimelineModel, TimelineEvent, TimelineEventType
from .attachment_model import AttachmentModel, AttachmentType

__all__ = [
    'EmailModel',
    'EvidenceModel',
    'EvidenceType',
    'EvidenceStatus',
    'TimelineModel',
    'TimelineEvent',
    'TimelineEventType',
    'AttachmentModel',
    'AttachmentType'
]
