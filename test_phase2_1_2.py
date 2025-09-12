"""
Phase 2.1-2.2 테스트: API 스캐너와 문서 생성기
"""
import sys
import time
from pathlib import Path

from src.docs import generate_all_documentation


def main():
    """Phase 2.1-2.2 테스트 실행"""
    print("🧪 Phase 2.1-2.2 시스템 테스트 시작")
    print("=" * 50)

    start_time = time.time()

    try:
        # 1. API 스캔 및 문서 생성 실행
        print("📚 API 스캔 및 문서 생성 실행...")

        result = generate_all_documentation()

        if result and 'generated_docs' in result:
            generated_docs = result['generated_docs']
            print(f"\n✅ 문서 생성 성공: {len(generated_docs)}개 파일")

            for doc_type, file_path in generated_docs.items():
                print(f"  - {doc_type}: {file_path}")

                # 파일 존재 여부 확인
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    print(f"    ✓ 파일 존재 ({file_size:,} bytes)")
                else:
                    print(f"    ❌ 파일 누락")

            # 스캔 결과 요약
            scan_result = result.get('scan_result', {})
            statistics = scan_result.get('statistics', {})
            print(f"\n📊 스캔 결과 요약:")
            print(f"  - 총 엔드포인트: {statistics.get('total_endpoints', 0)}개")
            print(f"  - 웹 라우트: {statistics.get('web_routes', 0)}개")
            print(f"  - API 라우트: {statistics.get('api_routes', 0)}개")
            print(f"  - 팩토리 라우트: {statistics.get('factory_routes', 0)}개")
            print(f"  - 데이터 모델: {statistics.get('total_models', 0)}개")

            print(f"\n⏱️ 총 실행 시간: {time.time() - start_time:.2f}초")
            print("🎉 Phase 2.1-2.2 테스트 완료")
            return True

        else:
            print("❌ 문서 생성 실패 - 결과 없음")
            return False

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
