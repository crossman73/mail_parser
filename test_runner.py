# test_runner.py
"""
프로젝트 전체 테스트 실행 스크립트
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """
    단위 테스트를 실행합니다.
    """
    print("🧪 단위 테스트 실행 중...")
    print("="*50)

    # 테스트 디스커버리 및 실행
    loader = unittest.TestLoader()
    start_dir = project_root / 'tests'
    suite = loader.discover(str(start_dir), pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*50)
    if result.wasSuccessful():
        print("✅ 모든 단위 테스트 통과!")
    else:
        print(
            f"❌ 테스트 실패: {len(result.failures)}개 실패, {len(result.errors)}개 오류")

    return result.wasSuccessful()


def check_dependencies():
    """
    의존성 패키지가 모두 설치되어 있는지 확인합니다.
    """
    print("\n📦 의존성 확인 중...")
    print("-"*30)

    required_packages = [
        'reportlab',
        'openpyxl',
        'psutil'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 설치됨")
        except ImportError:
            print(f"❌ {package}: 누락됨")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ 누락된 패키지가 있습니다: {', '.join(missing_packages)}")
        print("다음 명령으로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ 모든 의존성이 설치되어 있습니다.")
    return True


def validate_configuration():
    """
    설정 파일의 유효성을 검증합니다.
    """
    print("\n⚙️  설정 파일 검증 중...")
    print("-"*30)

    config_file = project_root / 'config.json'

    if not config_file.exists():
        print("❌ config.json 파일이 없습니다.")
        return False

    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 필수 키 확인
        required_keys = ['exclude_keywords', 'exclude_senders', 'date_range']
        for key in required_keys:
            if key not in config:
                print(f"❌ config.json에 필수 키가 없습니다: {key}")
                return False

        print("✅ config.json 파일이 유효합니다.")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ config.json 형식 오류: {str(e)}")
        return False


def check_project_structure():
    """
    프로젝트 구조가 올바른지 확인합니다.
    """
    print("\n📁 프로젝트 구조 확인 중...")
    print("-"*30)

    required_files = [
        'main.py',
        'config.json',
        'requirements.txt',
        'src/mail_parser/__init__.py',
        'src/mail_parser/processor.py',
        'src/mail_parser/analyzer.py',
        'src/mail_parser/formatter.py',
        'src/mail_parser/utils.py',
        'src/mail_parser/reporter.py'
    ]

    missing_files = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: 누락됨")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ 필수 파일이 누락되었습니다: {len(missing_files)}개")
        return False

    print("✅ 프로젝트 구조가 올바릅니다.")
    return True


def run_integration_test():
    """
    통합 테스트를 실행합니다.
    """
    print("\n🔗 통합 테스트 실행 중...")
    print("-"*30)

    # 간단한 통합 테스트: processor 초기화
    try:
        from src.mail_parser.processor import EmailEvidenceProcessor

        # 설정 파일로 프로세서 초기화
        config_path = project_root / 'config.json'
        processor = EmailEvidenceProcessor(str(config_path))

        print("✅ EmailEvidenceProcessor 초기화 성공")

        # 설정 로딩 확인
        if processor.config:
            print("✅ 설정 파일 로딩 성공")
        else:
            print("❌ 설정 파일 로딩 실패")
            return False

        return True

    except Exception as e:
        print(f"❌ 통합 테스트 실패: {str(e)}")
        return False


def run_performance_check():
    """
    기본적인 성능 체크를 수행합니다.
    """
    print("\n⚡ 성능 체크 실행 중...")
    print("-"*30)

    try:
        import psutil

        # 시스템 리소스 확인
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()

        print(f"💾 사용 가능한 메모리: {memory.available / 1024 / 1024 / 1024:.2f}GB")
        print(f"🔧 CPU 코어 수: {cpu_count}")

        # 메모리 부족 경고
        if memory.available < 1024 * 1024 * 1024:  # 1GB 미만
            print("⚠️  메모리가 부족할 수 있습니다. 대용량 mbox 파일 처리 시 주의하세요.")
        else:
            print("✅ 시스템 리소스가 충분합니다.")

        return True

    except Exception as e:
        print(f"❌ 성능 체크 실패: {str(e)}")
        return False


def generate_test_report():
    """
    테스트 결과 보고서를 생성합니다.
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.txt"

    # 여기서는 간단한 보고서만 생성
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 테스트 실행 보고서\n\n")
        f.write(f"실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"프로젝트: 법원 제출용 메일박스 증거 분류 시스템\n\n")
        f.write("테스트 결과는 콘솔 출력을 참조하세요.\n")

    print(f"\n📄 테스트 보고서 생성: {report_file}")


def main():
    """
    전체 테스트 스위트를 실행합니다.
    """
    print("🚀 프로젝트 검증 시작")
    print("="*60)

    success_count = 0
    total_tests = 5

    # 1. 프로젝트 구조 확인
    if check_project_structure():
        success_count += 1

    # 2. 의존성 확인
    if check_dependencies():
        success_count += 1

    # 3. 설정 파일 검증
    if validate_configuration():
        success_count += 1

    # 4. 통합 테스트
    if run_integration_test():
        success_count += 1

    # 5. 단위 테스트
    if run_unit_tests():
        success_count += 1

    # 성능 체크 (선택사항)
    run_performance_check()

    # 최종 결과
    print("\n" + "="*60)
    print("📊 검증 완료")
    print("="*60)
    print(f"✅ 통과: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("🎉 모든 검증이 통과되었습니다!")
        print("프로젝트가 정상적으로 작동할 준비가 되었습니다.")
        generate_test_report()
        return 0
    else:
        print(f"❌ {total_tests - success_count}개의 검증이 실패했습니다.")
        print("문제를 해결한 후 다시 실행하세요.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
