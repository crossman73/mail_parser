"""
Core services for the email evidence processing system.
"""

from .email_processor import EmailProcessor
from .evidence_manager import EvidenceManager
from .timeline_generator import TimelineGenerator
from .integrity_service import IntegrityService

__all__ = [
    'EmailProcessor',
    'EvidenceManager',
    'TimelineGenerator',
    'IntegrityService'
]
