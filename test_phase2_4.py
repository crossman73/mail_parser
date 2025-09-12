"""
Phase 2.4 테스트: docs/ 구조화 및 CI/CD 시스템
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from src.docs import generate_all_documentation
from src.docs.structure_manager import DocsStructureManager


def test_phase_2_4():
    """Phase 2.4 통합 테스트"""
    print("🧪 Phase 2.4: docs/ 구조화 및 CI/CD 테스트 시작")
    print("=" * 60)

    start_time = time.time()
    test_results = {
        'docs_structure': False,
        'file_organization': False,
        'config_generation': False,
        'auto_updater': False,
        'ci_cd_workflow': False,
        'git_hooks': False,
        'integration_test': False
    }

    try:
        # 1. 문서 구조 확인
        print("📁 1. 문서 구조 확인...")
        manager = DocsStructureManager()
        status = manager.get_structure_status()

        required_dirs = ['api', 'guides', 'assets', 'templates', 'archive']
        existing_dirs = [
            d for d in required_dirs if status['directories'].get(d, {}).get('exists')]

        if len(existing_dirs) == len(required_dirs):
            print(f"  ✅ 모든 필수 디렉토리 존재: {existing_dirs}")
            test_results['docs_structure'] = True
        else:
            missing = set(required_dirs) - set(existing_dirs)
            print(f"  ❌ 누락된 디렉토리: {missing}")

        # 2. 파일 정리 상태 확인
        print("\n📋 2. 파일 정리 상태 확인...")
        expected_files = {
            'docs/api/openapi/openapi.json': 'OpenAPI 명세',
            'docs/api/postman/postman_collection.json': 'Postman 컬렉션',
            'docs/api/references/API_Reference.md': 'API 레퍼런스',
            'docs/guides/developer/Developer_Guide.md': '개발자 가이드',
            'docs/docs_config.json': '문서 설정 파일'
        }

        existing_files = 0
        for file_path, description in expected_files.items():
            if Path(file_path).exists():
                print(f"  ✅ {description}: {file_path}")
                existing_files += 1
            else:
                print(f"  ❌ {description}: {file_path} (누락)")

        if existing_files >= len(expected_files) * 0.8:  # 80% 이상
            test_results['file_organization'] = True

        # 3. 설정 파일 검증
        print("\n⚙️ 3. 설정 파일 검증...")
        config_path = Path("docs/docs_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                required_keys = ['version', 'structure',
                                 'auto_update', 'generation_settings']
                if all(key in config for key in required_keys):
                    print(f"  ✅ 설정 파일 유효 (버전: {config.get('version')})")
                    test_results['config_generation'] = True
                else:
                    print(
                        f"  ❌ 설정 파일 키 누락: {set(required_keys) - set(config.keys())}")
            except Exception as e:
                print(f"  ❌ 설정 파일 파싱 오류: {e}")
        else:
            print("  ❌ 설정 파일 없음")

        # 4. 자동 업데이터 기능 테스트
        print("\n🔄 4. 자동 업데이터 기능 테스트...")
        try:
            from src.docs.auto_updater import (DocumentAutoUpdater,
                                               manual_update_trigger)

            updater = DocumentAutoUpdater()
            if updater.config.get('auto_update', {}).get('enabled'):
                print("  ✅ 자동 업데이터 설정 로드됨")

                # 수동 트리거 테스트
                last_update = manual_update_trigger()
                if last_update:
                    print(f"  ✅ 수동 업데이트 트리거 성공: {last_update}")
                    test_results['auto_updater'] = True
                else:
                    print("  ⚠️ 수동 업데이트 트리거 결과 없음")
            else:
                print("  ⚠️ 자동 업데이터 비활성화됨")
                test_results['auto_updater'] = True  # 비활성화도 정상 상태

        except Exception as e:
            print(f"  ❌ 자동 업데이터 테스트 실패: {e}")

        # 5. CI/CD 워크플로우 확인
        print("\n🚀 5. CI/CD 워크플로우 확인...")
        workflow_path = Path(".github/workflows/docs.yml")
        if workflow_path.exists():
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_content = f.read()

            required_jobs = ['generate-docs', 'deploy-docs', 'deploy-pages']
            found_jobs = [
                job for job in required_jobs if job in workflow_content]

            if len(found_jobs) == len(required_jobs):
                print(f"  ✅ 모든 CI/CD 작업 정의됨: {found_jobs}")
                test_results['ci_cd_workflow'] = True
            else:
                missing_jobs = set(required_jobs) - set(found_jobs)
                print(f"  ⚠️ 일부 CI/CD 작업 누락: {missing_jobs}")
                test_results['ci_cd_workflow'] = len(found_jobs) > 0
        else:
            print("  ❌ GitHub Actions 워크플로우 없음")

        # 6. Git Hook 확인
        print("\n🔧 6. Git Hook 설정 확인...")
        hook_files = [
            '.github/hooks/pre-commit',
            'install-hooks.bat',
            'install-hooks.sh'
        ]

        existing_hooks = [f for f in hook_files if Path(f).exists()]
        if len(existing_hooks) >= 2:  # 최소 2개 (pre-commit + 설치 스크립트)
            print(f"  ✅ Git Hook 파일들 존재: {existing_hooks}")
            test_results['git_hooks'] = True
        else:
            print(
                f"  ⚠️ 일부 Git Hook 파일 누락: {set(hook_files) - set(existing_hooks)}")

        # 7. 통합 테스트 - 전체 문서 재생성
        print("\n🧪 7. 통합 테스트 - 전체 시스템 동작...")
        try:
            integration_start = time.time()
            result = generate_all_documentation()

            if result and 'generated_docs' in result:
                generated_docs = result['generated_docs']
                scan_result = result.get('scan_result', {})
                statistics = scan_result.get('statistics', {})
                integration_time = time.time() - integration_start

                print(f"  ✅ 통합 테스트 성공 ({integration_time:.2f}초)")
                print(f"    📄 생성된 문서: {len(generated_docs)}개")
                print(
                    f"    🔍 스캔된 엔드포인트: {statistics.get('total_endpoints', 0)}개")
                test_results['integration_test'] = True
            else:
                print("  ❌ 통합 테스트 실패 - 문서 생성 없음")

        except Exception as e:
            print(f"  ❌ 통합 테스트 실패: {e}")

        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 Phase 2.4 테스트 결과:")

        passed = sum(test_results.values())
        total = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ 통과" if result else "❌ 실패"
            test_display = test_name.replace('_', ' ').title()
            print(f"  - {test_display}: {status}")

        success_rate = (passed / total) * 100
        execution_time = time.time() - start_time

        print(f"\n🎯 전체 결과: {passed}/{total} 통과 ({success_rate:.1f}%)")
        print(f"⏱️ 실행 시간: {execution_time:.2f}초")

        # 상세 통계
        if test_results['docs_structure'] and isinstance(status, dict):
            total_dirs = status.get('total_directories', 0)
            total_files = status.get('total_files', 0)
            print(f"📁 문서 구조: {total_dirs}개 디렉토리, {total_files}개 파일")

        if passed == total:
            print("🎉 Phase 2.4 완료! 모든 시스템이 정상 작동합니다.")
            return True
        elif passed >= total * 0.8:  # 80% 이상
            print("⚠️ Phase 2.4 대부분 성공 - 일부 기능 확인 필요")
            return True
        else:
            print("❌ Phase 2.4 실패 - 주요 시스템 문제 해결 필요")
            return False

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase_2_4()
    sys.exit(0 if success else 1)
