"""내보내기 기본 인터페이스"""

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict


class TimelineExporter(ABC):
    """타임라인 내보내기 추상 클래스"""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """내보내기 포맷 이름"""

    @property
    @abstractmethod
    def content_type(self) -> str:
        """MIME content type"""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """파일 확장자"""

    @abstractmethod
    def export(self, timeline: Dict[str, Any]) -> BytesIO:
        """타임라인 데이터를 BytesIO로 내보내기

        Args:
            timeline: TimelineService.get_timeline() 반환값
                {id, title, description, status, events: [{...}], ...}

        Returns:
            BytesIO: 생성된 파일 바이너리 스트림
        """

    def get_filename(self, timeline: Dict[str, Any]) -> str:
        """다운로드 파일명 생성"""
        title = timeline.get('title', '타임라인')
        # 파일명에 부적합한 문자 제거
        safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-()').strip()
        if not safe_title:
            safe_title = '타임라인'
        return f'{safe_title}.{self.file_extension}'
