#!/usr/bin/env python3
"""
Import 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== Import 테스트 시작 ===")

try:
    from src.legal_compliance.court_evidence_verifier import \
        CourtEvidenceIntegrityVerifier
    print("✅ CourtEvidenceIntegrityVerifier import 성공")
except Exception as e:
    print(f"❌ CourtEvidenceIntegrityVerifier import 실패: {e}")

try:
    from src.evidence.additional_evidence_manager import \
        AdditionalEvidenceManager
    print("✅ AdditionalEvidenceManager import 성공")
except Exception as e:
    print(f"❌ AdditionalEvidenceManager import 실패: {e}")

try:
    from src.timeline.integrated_timeline_generator import \
        IntegratedTimelineGenerator
    print("✅ IntegratedTimelineGenerator import 성공")
except Exception as e:
    print(f"❌ IntegratedTimelineGenerator import 실패: {e}")

try:
    from src.mail_parser.processor import EmailEvidenceProcessor
    print("✅ EmailEvidenceProcessor import 성공")
except Exception as e:
    print(f"❌ EmailEvidenceProcessor import 실패: {e}")

try:
    from src.web.app import create_app
    print("✅ create_app import 성공")
except Exception as e:
    print(f"❌ create_app import 실패: {e}")

print("=== Import 테스트 완료 ===")
