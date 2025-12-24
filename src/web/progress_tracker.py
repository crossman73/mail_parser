"""
실시간 처리 진행 상황 추적기
"""
import threading
import time
from datetime import datetime
from typing import Dict, Optional


class ProcessingTracker:
    """처리 진행 상황 추적 클래스"""

    def __init__(self):
        self._progress_data: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start_processing(self, task_id: str, task_name: str, total_steps: int = 100):
        """처리 시작"""
        with self._lock:
            self._progress_data[task_id] = {
                'task_name': task_name,
                'status': 'processing',
                'progress': 0,
                'total_steps': total_steps,
                'current_step': 0,
                'current_message': '처리를 시작합니다...',
                'started_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'error': None
            }

    def update_progress(self, task_id: str, step: int, message: str):
        """진행 상황 업데이트"""
        with self._lock:
            if task_id in self._progress_data:
                data = self._progress_data[task_id]
                data['current_step'] = step
                data['progress'] = min(100, (step / data['total_steps']) * 100)
                data['current_message'] = message
                data['updated_at'] = datetime.now().isoformat()

    def complete_processing(self, task_id: str, message: str = "처리가 완료되었습니다."):
        """처리 완료"""
        with self._lock:
            if task_id in self._progress_data:
                self._progress_data[task_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'current_message': message,
                    'completed_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })

    def set_error(self, task_id: str, error_message: str):
        """오류 설정"""
        with self._lock:
            if task_id in self._progress_data:
                self._progress_data[task_id].update({
                    'status': 'error',
                    'current_message': f'오류 발생: {error_message}',
                    'error': error_message,
                    'updated_at': datetime.now().isoformat()
                })

    def get_progress(self, task_id: str) -> Optional[Dict]:
        """진행 상황 조회"""
        with self._lock:
            return self._progress_data.get(task_id, None)

    def reset_stuck_tasks(self, max_stuck_minutes: int = 10):
        """멈춘 작업들을 오류 상태로 변경"""
        cutoff_time = datetime.now().timestamp() - (max_stuck_minutes * 60)

        with self._lock:
            for task_id, data in self._progress_data.items():
                if data.get('status') == 'processing':
                    updated_time = datetime.fromisoformat(
                        data['updated_at']).timestamp()
                    if updated_time < cutoff_time:
                        data.update({
                            'status': 'error',
                            'error': f'{max_stuck_minutes}분 이상 응답이 없어 비정상 종료로 판단됩니다.',
                            'updated_at': datetime.now().isoformat()
                        })

    def cleanup_error_tasks(self):
        """오류 상태의 작업들 정리"""
        with self._lock:
            to_remove = []
            for task_id, data in self._progress_data.items():
                if data.get('status') == 'error':
                    to_remove.append(task_id)

            for task_id in to_remove:
                del self._progress_data[task_id]

    def get_all_progress(self) -> Dict[str, Dict]:
        """모든 진행 상황 반환"""
        with self._lock:
            return self._progress_data.copy()

    def remove_task(self, task_id: str):
        """작업 제거"""
        with self._lock:
            self._progress_data.pop(task_id, None)

    def cleanup_old_tasks(self, max_age_minutes: int = 60):
        """오래된 작업 정리"""
        cutoff_time = datetime.now().timestamp() - (max_age_minutes * 60)

        with self._lock:
            to_remove = []
            for task_id, data in self._progress_data.items():
                updated_time = datetime.fromisoformat(
                    data['updated_at']).timestamp()
                if updated_time < cutoff_time:
                    to_remove.append(task_id)

            for task_id in to_remove:
                del self._progress_data[task_id]


# 전역 인스턴스
progress_tracker = ProcessingTracker()
