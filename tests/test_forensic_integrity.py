# tests/test_forensic_integrity.py
import os
import sys
import tempfile
import unittest
from pathlib import Path

from src.mail_parser.forensic_integrity import (ChainOfCustodyRecord,
                                                ForensicIntegrityService)

# 프로젝트 루트를 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestForensicIntegrity(unittest.TestCase):
    """포렌식 무결성 시스템 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.forensic_service = ForensicIntegrityService()

    def test_chain_of_custody_creation(self):
        """연계보관성 기록 생성 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_content = b"test email content for forensic verification"
            temp_file.write(test_content)
            temp_file.flush()

            try:
                record = self.forensic_service.create_chain_of_custody(
                    temp_file.name,
                    "테스트용 법정 증거"
                )

                # 기본 필드 검증
                self.assertIsNotNone(record.original_hash)
                self.assertEqual(len(record.original_hash), 64)  # SHA-256 길이
                self.assertIsNotNone(record.timestamp)
                self.assertIsNotNone(record.collector)
                self.assertEqual(record.verification_status, "VERIFIED")
                self.assertEqual(record.file_path, temp_file.name)
                self.assertEqual(record.file_size, len(test_content))
                self.assertEqual(record.notes, "테스트용 법정 증거")

                # 시스템 정보 검증
                self.assertIn('platform', record.system_info)
                self.assertIn('python_version', record.system_info)
                self.assertIn('hostname', record.system_info)

            finally:
                try:
                    temp_file.close()
                except Exception:
                    pass
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    def test_integrity_verification(self):
        """무결성 검증 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"original content for integrity test"
            temp_file.write(content)
            temp_file.flush()

            try:
                # 원본 해시 계산
                original_hash = self.forensic_service._calculate_sha256(
                    temp_file.name)

                # 무결성 검증 (성공 케이스)
                self.assertTrue(
                    self.forensic_service.verify_integrity(
                        temp_file.name, original_hash)
                )

                # 파일 수정
                with open(temp_file.name, 'ab') as f:
                    f.write(b" modified")

                # 무결성 검증 (실패 케이스)
                self.assertFalse(
                    self.forensic_service.verify_integrity(
                        temp_file.name, original_hash)
                )

            finally:
                try:
                    temp_file.close()
                except Exception:
                    pass
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    def test_custody_log_export(self):
        """연계보관성 로그 내보내기 테스트"""
        # 테스트 파일 생성
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()

            try:
                # 연계보관성 기록 생성
                self.forensic_service.create_chain_of_custody(temp_file.name)

                # 로그 내보내기
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as log_file:
                    # Close handle so export can write on Windows
                    log_file.close()
                    exported_path = self.forensic_service.export_custody_log(
                        log_file.name)

                    # 파일 생성 확인
                    self.assertTrue(os.path.exists(exported_path))

                    # JSON 내용 검증
                    import json
                    with open(exported_path, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)

                    self.assertIn('report_info', log_data)
                    self.assertIn('records', log_data)
                    self.assertEqual(len(log_data['records']), 1)

                    record = log_data['records'][0]
                    self.assertIn('original_hash', record)
                    self.assertIn('timestamp', record)
                    self.assertIn('collector', record)
                    self.assertIn('system_info', record)

                    os.unlink(exported_path)

            finally:
                try:
                    temp_file.close()
                except Exception:
                    pass
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    def test_custody_summary(self):
        """연계보관성 요약 테스트"""
        # 초기 상태 (기록 없음)
        summary = self.forensic_service.get_custody_summary()
        self.assertEqual(summary['total_records'], 0)
        self.assertEqual(summary['status'], 'No records')

        # 기록 추가 후
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test")
            temp_file.flush()

            try:
                self.forensic_service.create_chain_of_custody(temp_file.name)

                summary = self.forensic_service.get_custody_summary()
                self.assertEqual(summary['total_records'], 1)
                self.assertEqual(summary['verified_records'], 1)
                self.assertGreater(summary['total_file_size'], 0)
                self.assertIsInstance(summary['collectors'], list)

            finally:
                try:
                    temp_file.close()
                except Exception:
                    pass
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


class TestStreamingProcessor(unittest.TestCase):
    """스트리밍 프로세서 테스트"""

    def setUp(self):
        """테스트 설정"""
        from src.mail_parser.streaming_processor import StreamingEmailProcessor
        self.processor = StreamingEmailProcessor(
            chunk_size_mb=1, streaming_threshold_mb=1)

    def test_streaming_threshold(self):
        """스트리밍 임계값 테스트"""
        # 작은 파일 생성 (1MB 미만)
        with tempfile.NamedTemporaryFile(delete=False) as small_file:
            small_file.write(b"small content")
            small_file.flush()

            try:
                self.assertFalse(
                    self.processor.should_use_streaming(small_file.name))
            finally:
                try:
                    small_file.close()
                except Exception:
                    pass
                try:
                    os.unlink(small_file.name)
                except Exception:
                    pass

    def test_memory_monitoring(self):
        """메모리 모니터링 테스트"""
        memory_info = self.processor.get_memory_usage()

        # 기본 필드 존재 확인
        expected_fields = ['rss_mb', 'vms_mb', 'percent', 'available_mb']
        for field in expected_fields:
            self.assertIn(field, memory_info)
            self.assertIsInstance(memory_info[field], (int, float))

    def test_processing_statistics(self):
        """처리 통계 테스트"""
        stats = self.processor.get_processing_statistics()

        # 초기 상태 검증
        self.assertEqual(stats['processed_count'], 0)
        self.assertEqual(stats['error_count'], 0)
        self.assertEqual(stats['error_rate'], 0)
        self.assertIn('memory_usage', stats)


if __name__ == '__main__':
    # 로그 레벨 설정 (테스트 중 로그 출력 최소화)
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)

    # 테스트 실행
    unittest.main(verbosity=2)
