"""
API 문서 자동 생성 패키지

이 패키지는 프로젝트의 API와 코드를 자동으로 스캔하고
다양한 형식의 문서를 생성합니다.

주요 구성 요소:
- APIScanner: Flask 라우트와 API 스캔
- DocumentGenerator: 다양한 형식의 문서 생성
"""

from .api_scanner import APIScanner
from .doc_generator import DocumentGenerator
from .structure_manager import DocsStructureManager, reorganize_docs_structure
from .swagger_ui import SwaggerUIService, init_swagger_ui

__version__ = "2.0.0"
__author__ = "Email Evidence Processing Team"


def generate_all_documentation(project_root=None):
    """프로젝트 전체 문서 생성 (편의 함수)"""
    from pathlib import Path

    if project_root is None:
        project_root = Path(__file__).parent.parent.parent

    # API 스캔
    scanner = APIScanner(project_root)
    scan_result = scanner.scan_all_apis()

    # 문서 생성
    generator = DocumentGenerator()
    docs = generator.generate_all_docs(scan_result)

    return {
        'scan_result': scan_result,
        'generated_docs': docs
    }
