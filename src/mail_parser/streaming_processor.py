# src/mail_parser/streaming_processor.py
import gc
import logging
import mailbox
import os
from pathlib import Path
from typing import Dict, Iterator, Optional

try:
    import psutil
except Exception:
    psutil = None


class StreamingEmailProcessor:
    """대용량 mbox 파일 스트리밍 처리"""

    def __init__(self, chunk_size_mb: int = 64, streaming_threshold_mb: int = 500):
        self.chunk_size = chunk_size_mb * 1024 * 1024  # MB를 바이트로 변환
        self.streaming_threshold = streaming_threshold_mb * 1024 * 1024  # MB를 바이트로 변환
        self.logger = logging.getLogger(__name__)
        self.processed_count = 0
        self.error_count = 0

    def should_use_streaming(self, file_path: str) -> bool:
        """스트리밍 처리가 필요한지 판단"""
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            use_streaming = file_size > self.streaming_threshold

            if use_streaming:
                self.logger.info(
                    f"대용량 파일 감지 ({file_size_mb:.1f}MB), 스트리밍 모드 사용")
            else:
                self.logger.info(f"일반 크기 파일 ({file_size_mb:.1f}MB), 표준 모드 사용")

            return use_streaming
        except Exception as e:
            self.logger.error(f"파일 크기 확인 실패: {str(e)}")
            return False

    def stream_emails(self, mbox_path: str) -> Iterator[mailbox.Message]:
        """이메일 스트리밍 처리"""
        if not os.path.exists(mbox_path):
            raise FileNotFoundError(f"mbox 파일을 찾을 수 없습니다: {mbox_path}")

        self.processed_count = 0
        self.error_count = 0

        try:
            if not self.should_use_streaming(mbox_path):
                # 일반 처리
                yield from self._process_normal_mode(mbox_path)
            else:
                # 스트리밍 처리
                yield from self._process_streaming_mode(mbox_path)

        except Exception as e:
            self.logger.error(f"스트리밍 처리 중 심각한 오류: {str(e)}")
            raise

    def _process_normal_mode(self, mbox_path: str) -> Iterator[mailbox.Message]:
        """일반 모드 처리"""
        try:
            mbox = mailbox.mbox(mbox_path)
            for message in mbox:
                self.processed_count += 1
                yield message

        except Exception as e:
            self.logger.error(f"일반 모드 처리 실패: {str(e)}")
            raise

    def _process_streaming_mode(self, mbox_path: str) -> Iterator[mailbox.Message]:
        """스트리밍 모드 처리"""
        try:
            mbox = mailbox.mbox(mbox_path)

            for i, message in enumerate(mbox):
                self.processed_count += 1

                # 진행률 로그 (1000개마다)
                if i > 0 and i % 1000 == 0:
                    memory_info = self.get_memory_usage()
                    self.logger.info(
                        f"처리 진행률: {i:,}개 완료, "
                        f"메모리: {memory_info['rss_mb']:.1f}MB, "
                        f"오류: {self.error_count}개"
                    )

                    # 메모리 정리
                    if memory_info['rss_mb'] > 1024:  # 1GB 이상이면 가비지 컬렉션
                        gc.collect()

                # 메모리 임계값 체크
                if self.should_throttle_processing():
                    self.logger.warning("메모리 사용량이 높아 처리 속도를 조절합니다")
                    gc.collect()

                try:
                    yield message
                except Exception as e:
                    self.error_count += 1
                    self.logger.error(f"메시지 처리 중 오류 (#{i}): {str(e)}")
                    continue

        except MemoryError:
            self.logger.error("메모리 부족으로 스트리밍 처리 실패")
            raise
        except Exception as e:
            self.logger.error(f"스트리밍 처리 중 오류: {str(e)}")
            raise

    def get_memory_usage(self) -> Dict[str, float]:
        """메모리 사용량 모니터링"""
        try:
            if psutil is None:
                # psutil not installed; return best-effort zeros
                return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0, 'available_mb': 0}

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            self.logger.error(f"메모리 사용량 확인 실패: {str(e)}")
            return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0, 'available_mb': 0}

    def should_throttle_processing(self) -> bool:
        """처리 속도 조절이 필요한지 판단"""
        try:
            memory_info = self.get_memory_usage()
            # 메모리 사용률이 80% 이상이거나 사용량이 2GB 이상이면 조절
            return (memory_info['percent'] > 80.0 or
                    memory_info['rss_mb'] > 2048 or
                    memory_info['available_mb'] < 512)
        except Exception:
            return False

    def get_processing_statistics(self) -> Dict:
        """처리 통계 반환"""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'error_rate': (self.error_count / max(self.processed_count, 1)) * 100,
            'memory_usage': self.get_memory_usage()
        }
