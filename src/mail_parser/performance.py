# src/mail_parser/performance.py

import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

import psutil


class PerformanceMonitor:
    """
    성능 모니터링 클래스
    """

    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
        self.process = psutil.Process()
        self.memory_threshold_mb = 2048  # 2GB 임계값
        self.processing_metrics = {
            'emails_per_second': 0,
            'memory_peak_mb': 0,
            'disk_io_mb': 0,
            'error_rate': 0,
            'total_processed': 0,
            'total_errors': 0
        }

    def record_metric(self, name: str, value: Any):
        """
        성능 지표를 기록합니다.
        """
        self.metrics[name] = {
            'value': value,
            'timestamp': time.time(),
            'elapsed_since_start': time.time() - self.start_time
        }

    def get_memory_usage(self) -> Dict[str, float]:
        """
        현재 메모리 사용량을 반환합니다.
        """
        try:
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()

            current_usage_mb = memory_info.rss / 1024 / 1024

            # 메모리 피크 업데이트
            if current_usage_mb > self.processing_metrics['memory_peak_mb']:
                self.processing_metrics['memory_peak_mb'] = current_usage_mb

            return {
                'rss_mb': current_usage_mb,  # 물리 메모리
                'vms_mb': memory_info.vms / 1024 / 1024,  # 가상 메모리
                'percent': self.process.memory_percent(),
                'system_total_mb': system_memory.total / 1024 / 1024,
                'system_available_mb': system_memory.available / 1024 / 1024,
                'system_used_percent': system_memory.percent
            }
        except Exception:
            return {
                'rss_mb': 0, 'vms_mb': 0, 'percent': 0,
                'system_total_mb': 0, 'system_available_mb': 0, 'system_used_percent': 0
            }

    def monitor_streaming_performance(self, email_count: int, elapsed_time: float, error_count: int = 0):
        """스트리밍 처리 성능 모니터링"""
        try:
            emails_per_second = email_count / elapsed_time if elapsed_time > 0 else 0
            self.processing_metrics['emails_per_second'] = emails_per_second
            self.processing_metrics['total_processed'] = email_count
            self.processing_metrics['total_errors'] = error_count

            if email_count > 0:
                self.processing_metrics['error_rate'] = (
                    error_count / email_count) * 100

            # 메모리 사용량 체크
            current_memory = self.get_memory_usage()['rss_mb']
            if current_memory > self.memory_threshold_mb:
                self.record_metric('memory_warning', {
                    'current_mb': current_memory,
                    'threshold_mb': self.memory_threshold_mb,
                    'timestamp': time.time()
                })
        except Exception as e:
            print(f"성능 모니터링 중 오류: {e}")

    def should_throttle_processing(self) -> bool:
        """처리 속도 조절이 필요한지 판단"""
        try:
            memory_info = self.get_memory_usage()
            # 메모리 사용률이 80% 이상이거나 사용량이 임계값 이상이면 조절
            return (memory_info['percent'] > 80.0 or
                    memory_info['rss_mb'] > self.memory_threshold_mb * 0.8 or
                    memory_info['system_available_mb'] < 512)
        except Exception:
            return False

    def get_performance_summary(self) -> Dict:
        """성능 요약 정보 반환"""
        current_memory = self.get_memory_usage()
        elapsed_total = time.time() - self.start_time

        return {
            'total_runtime_seconds': elapsed_total,
            'current_memory': current_memory,
            'processing_metrics': self.processing_metrics,
            'peak_memory_mb': self.processing_metrics['memory_peak_mb'],
            'average_emails_per_second': self.processing_metrics['emails_per_second'],
            'error_rate_percent': self.processing_metrics['error_rate'],
            'memory_efficiency': self._calculate_memory_efficiency()
        }

    def _calculate_memory_efficiency(self) -> str:
        """메모리 효율성 등급 계산"""
        peak_mb = self.processing_metrics['memory_peak_mb']

        if peak_mb < 256:
            return 'Excellent'
        elif peak_mb < 512:
            return 'Good'
        elif peak_mb < 1024:
            return 'Fair'
        elif peak_mb < 2048:
            return 'Poor'
        else:
            return 'Critical'

    def get_cpu_usage(self) -> float:
        """
        현재 CPU 사용률을 반환합니다.
        """
        return self.process.cpu_percent()

    def record_system_metrics(self, stage: str):
        """
        시스템 지표를 기록합니다.
        """
        memory = self.get_memory_usage()
        cpu = self.get_cpu_usage()

        self.record_metric(f'{stage}_memory_rss_mb', memory['rss_mb'])
        self.record_metric(f'{stage}_memory_percent', memory['percent'])
        self.record_metric(f'{stage}_cpu_percent', cpu)

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        성능 요약 정보를 반환합니다.
        """
        total_time = time.time() - self.start_time
        current_memory = self.get_memory_usage()

        return {
            'total_runtime_seconds': total_time,
            'current_memory_mb': current_memory['rss_mb'],
            'peak_memory_mb': max([m['value'] for k, m in self.metrics.items()
                                   if 'memory_rss_mb' in k], default=0),
            'metrics_count': len(self.metrics),
            'all_metrics': self.metrics
        }


def timing_decorator(func):
    """
    함수 실행 시간을 측정하는 데코레이터
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        print(f"⏱️  {func.__name__}: {end_time - start_time:.2f}초")
        return result

    return wrapper


@contextmanager
def performance_context(operation_name: str, monitor: Optional[PerformanceMonitor] = None):
    """
    성능 측정을 위한 컨텍스트 매니저
    """
    if monitor is None:
        monitor = PerformanceMonitor()

    start_time = time.time()
    start_memory = monitor.get_memory_usage()

    print(f"🚀 {operation_name} 시작...")

    try:
        yield monitor
    finally:
        end_time = time.time()
        end_memory = monitor.get_memory_usage()

        duration = end_time - start_time
        memory_delta = end_memory['rss_mb'] - start_memory['rss_mb']

        print(f"✅ {operation_name} 완료")
        print(f"   소요 시간: {duration:.2f}초")
        print(f"   메모리 증가: {memory_delta:+.1f}MB")

        monitor.record_metric(f'{operation_name}_duration', duration)
        monitor.record_metric(f'{operation_name}_memory_delta', memory_delta)


class EmailProcessingOptimizer:
    """
    이메일 처리 최적화를 위한 클래스
    """

    @staticmethod
    def should_use_streaming(file_size_mb: float) -> bool:
        """
        파일 크기에 따라 스트리밍 처리 여부를 결정합니다.
        """
        return file_size_mb > 500  # 500MB 이상이면 스트리밍

    @staticmethod
    def get_optimal_chunk_size(file_size_mb: float) -> int:
        """
        파일 크기에 따른 최적 청크 크기를 계산합니다.
        """
        if file_size_mb < 10:
            return 8192  # 8KB
        elif file_size_mb < 100:
            return 65536  # 64KB
        elif file_size_mb < 500:
            return 524288  # 512KB
        else:
            return 1048576  # 1MB

    @staticmethod
    def estimate_memory_usage(email_count: int, avg_email_size_kb: float = 50) -> float:
        """
        예상 메모리 사용량을 계산합니다 (MB 단위).
        """
        # 이메일 처리 시 대략적인 메모리 배수
        memory_multiplier = 3  # 원본 + 파싱 + 변환

        total_size_mb = (email_count * avg_email_size_kb *
                         memory_multiplier) / 1024
        overhead_mb = 100  # 프로그램 기본 오버헤드

        return total_size_mb + overhead_mb

    @staticmethod
    def get_processing_recommendations(email_count: int, total_size_mb: float) -> Dict[str, Any]:
        """
        처리 방식 추천을 제공합니다.
        """
        available_memory_mb = psutil.virtual_memory().available / 1024 / 1024
        estimated_usage = EmailProcessingOptimizer.estimate_memory_usage(
            email_count)

        recommendations = {
            'use_streaming': EmailProcessingOptimizer.should_use_streaming(total_size_mb),
            'chunk_size': EmailProcessingOptimizer.get_optimal_chunk_size(total_size_mb),
            'estimated_memory_mb': estimated_usage,
            'available_memory_mb': available_memory_mb,
            'memory_sufficient': estimated_usage < available_memory_mb * 0.8,
            'suggestions': []
        }

        if not recommendations['memory_sufficient']:
            recommendations['suggestions'].append(
                "메모리가 부족할 수 있습니다. 배치 처리 모드를 사용하세요."
            )

        if total_size_mb > 500:
            recommendations['suggestions'].append(
                "대용량 파일입니다. 처리 시간이 오래 걸릴 수 있습니다."
            )

        if email_count > 1000:
            recommendations['suggestions'].append(
                "대량의 이메일입니다. 진행률 표시를 활성화하는 것을 권장합니다."
            )

        return recommendations


def log_performance_metrics(monitor: PerformanceMonitor, output_file: str = None):
    """
    성능 지표를 로그 파일에 기록합니다.
    """
    import json
    from datetime import datetime

    summary = monitor.get_performance_summary()

    performance_log = {
        'timestamp': datetime.now().isoformat(),
        'summary': summary,
        'system_info': {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'platform': os.name
        }
    }

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"performance_log_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(performance_log, f, indent=2, ensure_ascii=False)

    print(f"📊 성능 로그가 저장되었습니다: {output_file}")
    return output_file
