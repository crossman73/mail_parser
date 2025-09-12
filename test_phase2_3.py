"""
Phase 2.3 테스트: Swagger UI 통합 시스템
"""
import signal
import sys
import threading
import time
from pathlib import Path

import requests

from src.docs import generate_all_documentation
from src.web.app_factory import create_app


def test_swagger_ui_integration():
    """Swagger UI 통합 테스트"""
    print("🧪 Phase 2.3: Swagger UI 통합 테스트 시작")
    print("=" * 50)

    start_time = time.time()
    test_results = {
        'swagger_ui_service': False,
        'openapi_json_serving': False,
        'docs_dashboard': False,
        'docs_regeneration': False,
        'web_integration': False
    }

    try:
        # 1. 기본 문서가 있는지 확인
        print("📚 1. 기본 문서 존재 확인...")
        docs_dir = Path("docs")
        openapi_file = docs_dir / "openapi.json"

        if not openapi_file.exists():
            print("  📄 OpenAPI 파일이 없음, 생성 중...")
            result = generate_all_documentation()
            if result and 'generated_docs' in result:
                print("  ✅ 기본 문서 생성 완료")
            else:
                print("  ❌ 기본 문서 생성 실패")
                return test_results

        # 2. Flask 앱 생성 및 Swagger UI 서비스 테스트
        print("\n🏭 2. Flask 앱 생성 및 Swagger UI 통합...")
        try:
            app = create_app()

            # Swagger UI 서비스가 등록되었는지 확인
            with app.app_context():
                # 라우트 확인
                routes = [rule.rule for rule in app.url_map.iter_rules()]
                swagger_routes = [
                    r for r in routes if 'swagger' in r or 'openapi' in r]

                if swagger_routes:
                    print(f"  ✅ Swagger UI 라우트 등록됨: {swagger_routes}")
                    test_results['swagger_ui_service'] = True
                else:
                    print("  ❌ Swagger UI 라우트 없음")

        except Exception as e:
            print(f"  ❌ Flask 앱 생성 실패: {e}")
            return test_results

        # 3. 테스트 서버 시작
        print("\n🚀 3. 테스트 서버 시작...")
        server_thread = None
        server_started = False

        def run_server():
            nonlocal server_started
            try:
                app.run(host='127.0.0.1', port=5555,
                        debug=False, use_reloader=False)
                server_started = True
            except Exception as e:
                print(f"  ❌ 서버 시작 실패: {e}")

        try:
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(3)  # 서버 시작 대기

            base_url = "http://127.0.0.1:5555"

            # 4. Swagger UI 페이지 테스트
            print("\n🔌 4. Swagger UI 페이지 접근 테스트...")
            try:
                response = requests.get(
                    f"{base_url}/api/swagger-ui", timeout=5)
                if response.status_code == 200 and 'swagger-ui' in response.text.lower():
                    print("  ✅ Swagger UI 페이지 로드 성공")
                    test_results['web_integration'] = True
                else:
                    print(f"  ❌ Swagger UI 페이지 오류: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Swagger UI 접근 실패: {e}")

            # 5. OpenAPI JSON 서빙 테스트
            print("\n📋 5. OpenAPI JSON 서빙 테스트...")
            try:
                response = requests.get(
                    f"{base_url}/api/openapi.json", timeout=5)
                if response.status_code == 200:
                    openapi_data = response.json()
                    if 'openapi' in openapi_data and 'paths' in openapi_data:
                        print(
                            f"  ✅ OpenAPI JSON 서빙 성공 ({len(openapi_data['paths'])}개 경로)")
                        test_results['openapi_json_serving'] = True
                    else:
                        print("  ❌ OpenAPI JSON 형식 오류")
                else:
                    print(f"  ❌ OpenAPI JSON 서빙 실패: {response.status_code}")
            except Exception as e:
                print(f"  ❌ OpenAPI JSON 접근 실패: {e}")

            # 6. 문서 대시보드 테스트
            print("\n📊 6. 문서 대시보드 테스트...")
            try:
                response = requests.get(
                    f"{base_url}/api/docs-dashboard", timeout=5)
                if response.status_code == 200 and '대시보드' in response.text:
                    print("  ✅ 문서 대시보드 로드 성공")
                    test_results['docs_dashboard'] = True
                else:
                    print(f"  ❌ 문서 대시보드 오류: {response.status_code}")
            except Exception as e:
                print(f"  ❌ 문서 대시보드 접근 실패: {e}")

            # 7. 문서 재생성 API 테스트
            print("\n🔄 7. 문서 재생성 API 테스트...")
            try:
                response = requests.post(
                    f"{base_url}/api/regenerate-docs", timeout=10)
                if response.status_code == 200:
                    result_data = response.json()
                    if result_data.get('success'):
                        print(f"  ✅ 문서 재생성 성공: {result_data.get('message')}")
                        test_results['docs_regeneration'] = True
                    else:
                        print(f"  ❌ 문서 재생성 실패: {result_data.get('message')}")
                else:
                    print(f"  ❌ 문서 재생성 API 오류: {response.status_code}")
            except Exception as e:
                print(f"  ❌ 문서 재생성 API 접근 실패: {e}")

        finally:
            # 서버 종료는 데몬 스레드이므로 자동으로 종료됨
            pass

        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 Phase 2.3 테스트 결과:")

        passed = sum(test_results.values())
        total = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ 통과" if result else "❌ 실패"
            print(f"  - {test_name}: {status}")

        success_rate = (passed / total) * 100
        execution_time = time.time() - start_time

        print(f"\n🎯 전체 결과: {passed}/{total} 통과 ({success_rate:.1f}%)")
        print(f"⏱️ 실행 시간: {execution_time:.2f}초")

        if passed == total:
            print("🎉 Phase 2.3 Swagger UI 통합 완료!")
            return True
        else:
            print("⚠️ 일부 테스트 실패 - 확인 필요")
            return False

    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다")
        return False
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_swagger_ui_integration()
    sys.exit(0 if success else 1)
