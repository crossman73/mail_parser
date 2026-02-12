"""
Core services for the email evidence processing system.
"""

from .email_processor import EmailProcessor
from .evidence_manager import EvidenceManager
from ...core.services.timeline_generator import TimelineGenerator
from ...core.services.integrity_service import IntegrityService

__all__ = [
    'EmailProcessor',
    'EvidenceManager',
    'TimelineGenerator',
    'IntegrityService'
]
