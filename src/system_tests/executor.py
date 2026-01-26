"""
시스템 테스트 실행기
"""
import importlib
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict


class TestExecutor:
    """테스트 실행기"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))

    def execute_test(self, test_module: str, test_function: str,
                    timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        테스트 실행

        Args:
            test_module: 모듈 경로 (예: 'src.system_tests.core_tests')
            test_function: 함수명 (예: 'test_web_routes')
            timeout_seconds: 타임아웃 (초)

        Returns:
            실행 결과 딕셔너리
        """
        start_time = time.time()
        result = {
            'status': 'unknown',
            'message': '',
            'error_detail': '',
            'duration_ms': 0
        }

        try:
            # 모듈 임포트
            module = importlib.import_module(test_module)

            # 함수 가져오기
            if not hasattr(module, test_function):
                result['status'] = 'error'
                result['message'] = f'함수를 찾을 수 없습니다: {test_function}'
                return result

            test_func = getattr(module, test_function)

            # 테스트 실행
            test_result = test_func()

            # 실행 시간 계산
            duration_ms = int((time.time() - start_time) * 1000)
            result['duration_ms'] = duration_ms

            # 결과 처리
            if isinstance(test_result, dict):
                # 딕셔너리 형태의 결과
                result['status'] = test_result.get('status', 'success')
                result['message'] = test_result.get('message', '테스트 통과')
            elif isinstance(test_result, bool):
                # 불린 형태의 결과
                result['status'] = 'success' if test_result else 'failed'
                result['message'] = '테스트 통과' if test_result else '테스트 실패'
            else:
                # 기타 결과는 성공으로 간주
                result['status'] = 'success'
                result['message'] = str(test_result) if test_result else '테스트 통과'

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            result['duration_ms'] = duration_ms
            result['status'] = 'error'
            result['message'] = str(e)
            result['error_detail'] = traceback.format_exc()

        return result

    def execute_multiple_tests(self, tests: list) -> Dict[str, Any]:
        """
        여러 테스트 실행

        Args:
            tests: 테스트 정보 리스트

        Returns:
            전체 실행 결과
        """
        results = []
        total_start = time.time()

        for test_info in tests:
            test_result = self.execute_test(
                test_info['test_module'],
                test_info['test_function'],
                test_info.get('timeout_seconds', 30)
            )

            results.append({
                'test_key': test_info['test_key'],
                'test_name': test_info['test_name'],
                **test_result
            })

        total_duration = int((time.time() - total_start) * 1000)

        # 통계 계산
        total = len(results)
        success = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        error = sum(1 for r in results if r['status'] == 'error')

        return {
            'total': total,
            'success': success,
            'failed': failed,
            'error': error,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'total_duration_ms': total_duration,
            'results': results
        }


# 전역 실행기 인스턴스
test_executor = TestExecutor()
