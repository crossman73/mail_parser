#!/usr/bin/env python3
"""
통합 테스트: 전체 시스템 작동 검증
"""

import os
import sys

sys.path.append('.')


def test_flask_app_creation():
    """Flask 애플리케이션 생성 테스트"""
    try:
        from src.web.app_factory import create_app
        app = create_app()
        rules = list(app.url_map.iter_rules())

        print("✅ Flask 애플리케이션 생성 성공")
        print(f"📍 등록된 라우트 수: {len(rules)}개")

        # 주요 라우트 확인
        key_routes = []
        for rule in rules:
            methods = ', '.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
            key_routes.append(f"[{methods}] {rule.rule}")

        print("주요 라우트 (처음 10개):")
        for route in key_routes[:10]:
            print(f"  - {route}")

        return True, len(rules)
    except Exception as e:
        print(f"❌ Flask 앱 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def test_docs_system():
    """문서화 시스템 테스트"""
    try:
        from pathlib import Path

        from src.docs.api_scanner import APIScanner
        from src.docs.doc_generator import DocumentGenerator

        # API 스캔
        project_root = Path('.')
        scanner = APIScanner(project_root)
        endpoints = scanner.scan_all_apis()

        # 문서 생성
        doc_gen = DocumentGenerator()
        results = doc_gen.generate_all_docs(endpoints)

        print(f"✅ 문서화 시스템 작동: {len(endpoints)}개 엔드포인트, {len(results)}개 문서")
        return True
    except Exception as e:
        print(f"❌ 문서화 시스템 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_swagger_ui():
    """Swagger UI 시스템 테스트"""
    try:
        from src.docs.swagger_ui import SwaggerUIService

        swagger_service = SwaggerUIService()

        # OpenAPI 스펙 로드 테스트
        if os.path.exists('docs/openapi.json'):
            print("✅ Swagger UI 시스템 준비 완료")
            return True
        else:
            print("⚠️ OpenAPI 스펙 파일 없음")
            return False
    except Exception as e:
        print(f"❌ Swagger UI 시스템 실패: {e}")
        return False


def main():
    """통합 테스트 실행"""
    print("🚀 전체 시스템 통합 테스트 시작")
    print("=" * 50)

    results = []

    # 1. Flask 앱 테스트
    print("\n1️⃣ Flask 애플리케이션 테스트")
    flask_success, route_count = test_flask_app_creation()
    results.append(("Flask App", flask_success))

    # 2. 문서화 시스템 테스트
    print("\n2️⃣ 문서화 시스템 테스트")
    docs_success = test_docs_system()
    results.append(("Documentation System", docs_success))

    # 3. Swagger UI 테스트
    print("\n3️⃣ Swagger UI 시스템 테스트")
    swagger_success = test_swagger_ui()
    results.append(("Swagger UI", swagger_success))

    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 통합 테스트 결과")
    print("=" * 50)

    success_count = 0
    for test_name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"  - {test_name}: {status}")
        if success:
            success_count += 1

    print(
        f"\n🎯 전체 결과: {success_count}/{len(results)} 통과 ({100*success_count/len(results):.1f}%)")

    if success_count == len(results):
        print("🎉 모든 시스템이 정상 작동합니다!")
        return 0
    else:
        print("⚠️ 일부 시스템에 문제가 있습니다.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
