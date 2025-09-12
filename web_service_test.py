#!/usr/bin/env python3
"""
웹 서비스 자동 테스트 스크립트
requests를 사용한 HTTP 테스트
"""

import sys
import time
from urllib.parse import urljoin

import requests


class WebServiceTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_endpoint(self, path, expected_status=200, timeout=10):
        """개별 엔드포인트 테스트"""
        url = urljoin(self.base_url, path)
        try:
            response = self.session.get(url, timeout=timeout)

            success = response.status_code == expected_status
            result = {
                'url': url,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'success': success,
                'size': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'response_time': response.elapsed.total_seconds()
            }

            return result

        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'status_code': None,
                'size': 0
            }

    def test_all_endpoints(self):
        """모든 주요 엔드포인트 테스트"""
        endpoints = [
            ('/', 200, '메인 페이지'),
            ('/docs', 200, '문서 페이지'),
            ('/swagger', 200, 'Swagger UI'),
            ('/api', 200, 'API 인덱스'),
            ('/api/docs', 200, 'API 문서'),
            ('/api/openapi.json', 200, 'OpenAPI JSON'),
            ('/health', 200, '헬스체크'),
            ('/api/endpoints', 404, '존재하지 않는 엔드포인트 (404 예상)'),  # 이건 404가 정상
        ]

        print("🚀 웹 서비스 자동 테스트 시작")
        print("=" * 60)

        results = []
        success_count = 0

        for path, expected_status, description in endpoints:
            print(f"\n🔍 테스트 중: {description}")
            print(f"   URL: {urljoin(self.base_url, path)}")

            result = self.test_endpoint(path, expected_status)
            results.append((description, result))

            if result['success']:
                print(
                    f"   ✅ 성공: {result['status_code']} ({result['size']} bytes, {result['response_time']:.2f}s)")
                success_count += 1
            else:
                if 'error' in result:
                    print(f"   ❌ 연결 실패: {result['error']}")
                else:
                    print(
                        f"   ❌ 실패: {result['status_code']} (예상: {result['expected_status']})")

        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)

        for description, result in results:
            status = "✅ 통과" if result['success'] else "❌ 실패"
            print(f"  - {description}: {status}")

        print(
            f"\n🎯 전체 결과: {success_count}/{len(endpoints)} 통과 ({100*success_count/len(endpoints):.1f}%)")

        if success_count == len(endpoints):
            print("🎉 모든 테스트가 성공했습니다!")
            return True
        else:
            print("⚠️ 일부 테스트가 실패했습니다.")
            return False


def main():
    print("⏰ 서버 시작 대기 중... (5초)")
    time.sleep(5)  # 서버가 완전히 시작될 때까지 대기

    tester = WebServiceTester()
    success = tester.test_all_endpoints()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
