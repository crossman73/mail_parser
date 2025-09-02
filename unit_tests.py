#!/usr/bin/env python3
"""
단위 테스트 - 모듈 import 및 기본 기능 검증
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestModuleImports(unittest.TestCase):
    """모듈 import 테스트"""

    def test_court_evidence_verifier_import(self):
        """CourtEvidenceIntegrityVerifier import 테스트"""
        try:
            from src.legal_compliance.court_evidence_verifier import \
                CourtEvidenceIntegrityVerifier
            self.assertTrue(True, "CourtEvidenceIntegrityVerifier import 성공")
        except ImportError as e:
            self.fail(f"CourtEvidenceIntegrityVerifier import 실패: {e}")

    def test_additional_evidence_manager_import(self):
        """AdditionalEvidenceManager import 테스트"""
        try:
            from src.evidence.additional_evidence_manager import \
                AdditionalEvidenceManager
            self.assertTrue(True, "AdditionalEvidenceManager import 성공")
        except ImportError as e:
            self.fail(f"AdditionalEvidenceManager import 실패: {e}")

    def test_integrated_timeline_generator_import(self):
        """IntegratedTimelineGenerator import 테스트"""
        try:
            from src.timeline.integrated_timeline_generator import \
                IntegratedTimelineGenerator
            self.assertTrue(True, "IntegratedTimelineGenerator import 성공")
        except ImportError as e:
            self.fail(f"IntegratedTimelineGenerator import 실패: {e}")


class TestCourtEvidenceVerifier(unittest.TestCase):
    """CourtEvidenceIntegrityVerifier 기능 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        from src.legal_compliance.court_evidence_verifier import \
            CourtEvidenceIntegrityVerifier
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = CourtEvidenceIntegrityVerifier(self.temp_dir)

    def test_verifier_initialization(self):
        """검증기 초기화 테스트"""
        self.assertIsNotNone(self.verifier)
        self.assertEqual(
            str(self.verifier.processed_emails_dir), self.temp_dir)

    def test_file_hash_calculation(self):
        """파일 해시 계산 테스트"""
        # 테스트 파일 생성
        test_file = Path(self.temp_dir) / "test.txt"
        test_content = "테스트 내용"

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        # 해시 계산
        file_hash = self.verifier.calculate_file_hash(test_file)

        # 해시가 올바르게 계산되었는지 확인
        self.assertIsNotNone(file_hash)
        self.assertEqual(len(file_hash), 64)  # SHA-256은 64자리 hex


class TestAdditionalEvidenceManager(unittest.TestCase):
    """AdditionalEvidenceManager 기능 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        from src.evidence.additional_evidence_manager import \
            AdditionalEvidenceManager
        self.temp_dir = tempfile.mkdtemp()
        self.manager = AdditionalEvidenceManager(base_dir=self.temp_dir)

    def test_manager_initialization(self):
        """매니저 초기화 테스트"""
        self.assertIsNotNone(self.manager)
        self.assertTrue(self.manager.additional_evidence_dir.exists())


class TestIntegratedTimelineGenerator(unittest.TestCase):
    """IntegratedTimelineGenerator 기능 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        from src.timeline.integrated_timeline_generator import \
            IntegratedTimelineGenerator
        self.temp_dir = tempfile.mkdtemp()
        self.generator = IntegratedTimelineGenerator(self.temp_dir)

    def test_generator_initialization(self):
        """생성기 초기화 테스트"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(str(self.generator.base_dir), self.temp_dir)


class TestWebApp(unittest.TestCase):
    """웹 애플리케이션 테스트"""

    def test_app_creation(self):
        """Flask 앱 생성 테스트"""
        try:
            from src.web.app import create_app
            app = create_app()
            self.assertIsNotNone(app)
            self.assertTrue(True, "Flask 앱 생성 성공")
        except Exception as e:
            self.fail(f"Flask 앱 생성 실패: {e}")


def run_unit_tests():
    """단위 테스트 실행"""
    print("=" * 60)
    print("🧪 단위 테스트 시작")
    print("=" * 60)

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 클래스들 추가
    suite.addTest(loader.loadTestsFromTestCase(TestModuleImports))
    suite.addTest(loader.loadTestsFromTestCase(TestCourtEvidenceVerifier))
    suite.addTest(loader.loadTestsFromTestCase(TestAdditionalEvidenceManager))
    suite.addTest(loader.loadTestsFromTestCase(
        TestIntegratedTimelineGenerator))
    suite.addTest(loader.loadTestsFromTestCase(TestWebApp))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 60)
    if result.wasSuccessful():
        print("✅ 모든 단위 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
        print(f"실패: {len(result.failures)}, 오류: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)
