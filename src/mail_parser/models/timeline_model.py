"""
Timeline models re-export.
src.core.models.timeline_model에서 정의된 모델을 mail_parser에서 사용.
"""

from src.core.models.timeline_model import (
    TimelineModel,
    TimelineEvent,
    TimelineEventType,
)

__all__ = [
    'TimelineModel',
    'TimelineEvent',
    'TimelineEventType',
]
