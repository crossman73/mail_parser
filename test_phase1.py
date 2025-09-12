"""
Phase 1 검증 스크립트 - 통합 아키텍처 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path.cwd()))


def test_phase1():
    """Phase 1 구현 사항 검증"""
    print("🧪 Phase 1 검증 시작...")

    results = {
        'unified_architecture': False,
        'web_factory': False,
        'main_integration': False,
        'template_update': False,
        'system_initialization': False
    }

    # 1. Unified Architecture 테스트
    try:
        from src.core.unified_architecture import (SystemConfig,
                                                   UnifiedArchitecture)

        # 기본 설정으로 초기화 테스트
        config = SystemConfig(
            project_root=Path.cwd(),
            config_data={},
            app_name="테스트 시스템",
            version="2.0.0"
        )

        arch = UnifiedArchitecture(config)
        arch.initialize()

        # 상태 확인
        status = arch.get_system_status()
        print(
            f"✅ Unified Architecture: {status['app_name']} v{status['version']}")
        results['unified_architecture'] = True

        arch.cleanup()

    except Exception as e:
        print(f"❌ Unified Architecture 실패: {e}")

    # 2. Web Factory 테스트
    try:
        from src.web.app_factory import create_app

        app = create_app()
        print(f"✅ Web Factory: Flask 앱 생성 성공")
        results['web_factory'] = True

    except Exception as e:
        print(f"❌ Web Factory 실패: {e}")

    # 3. Main 통합 테스트
    try:
        import main
        print(f"✅ Main Integration: main.py 임포트 성공")
        results['main_integration'] = True

    except Exception as e:
        print(f"❌ Main Integration 실패: {e}")

    # 4. 템플릿 확인
    try:
        template_path = Path('templates/index.html')
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Unified Architecture' in content:
                    print("✅ Template Update: 템플릿 업데이트 완료")
                    results['template_update'] = True
                else:
                    print("❌ Template Update: 템플릿 내용 확인 필요")
        else:
            print("❌ Template Update: 템플릿 파일 없음")

    except Exception as e:
        print(f"❌ Template Update 실패: {e}")

    # 5. 전체 시스템 초기화 테스트
    try:
        # 설정 로드
        import json

        from src.core.unified_architecture import (SystemConfig,
                                                   UnifiedArchitecture)
        from src.web.app_factory import create_app
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except:
            config_data = {}

        config = SystemConfig(
            project_root=Path.cwd(),
            config_data=config_data,
            app_name="이메일 증거 처리 시스템",
            version="2.0.0"
        )

        arch = UnifiedArchitecture(config)
        arch.initialize()

        app = create_app(arch)

        print("✅ System Integration: 전체 시스템 초기화 성공")
        results['system_initialization'] = True

        arch.cleanup()

    except Exception as e:
        print(f"❌ System Integration 실패: {e}")

    # 결과 요약
    print(f"\n📊 Phase 1 검증 결과:")
    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\n🎯 전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 Phase 1 구현 완료! 웹 서버 시작 준비됨")
        return True
    else:
        print("⚠️ 일부 테스트 실패, 수정 필요")
        return False


if __name__ == "__main__":
    success = test_phase1()
    sys.exit(0 if success else 1)
