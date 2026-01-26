#!/usr/bin/env python
"""
통합 웹 애플리케이션 실행 스크립트
Unified web application runner
"""

import os
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_and_install_dependencies():
    """의존성 패키지 확인 및 설치"""
    print("📦 의존성 패키지 확인 중...")

    # requirements.txt 파일 확인
    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        return False

    # 필수 패키지 목록
    required_packages = {
        'flask': 'Flask>=2.0.0',
        'reportlab': 'reportlab>=3.6.0',
        'openpyxl': 'openpyxl>=3.0.0',
        'psutil': 'psutil>=5.8.0'
    }

    missing_packages = []

    # 각 패키지 확인
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
            print(f"✅ {package_name} - 설치됨")
        except ImportError:
            print(f"❌ {package_name} - 설치 필요")
            missing_packages.append(package_spec)

    # 누락된 패키지가 있으면 설치
    if missing_packages:
        print(f"\n🔧 누락된 패키지 설치 중: {', '.join(missing_packages)}")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True)
            print("✅ 모든 의존성 패키지 설치 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 패키지 설치 실패: {e}")
            print(f"출력: {e.stdout}")
            print(f"에러: {e.stderr}")
            print("\n수동으로 설치해주세요:")
            print(f"  {sys.executable} -m pip install -r requirements.txt")
            return False
    else:
        print("✅ 모든 의존성 패키지가 설치되어 있습니다.")
        return True


try:
    # 먼저 의존성 확인 및 설치
    if not check_and_install_dependencies():
        print("❌ 의존성 패키지 설치에 실패했습니다. 프로그램을 종료합니다.")
        sys.exit(1)

    # 의존성 설치 후 Flask 앱 import
    from src.web.app import create_app

    def main():
        """메인 실행 함수"""
        print("=" * 60)
        print("📧 이메일 증거 처리 시스템 웹 서버")
        print("=" * 60)

        # 환경 확인
        config_file = project_root / "config.json"
        if not config_file.exists():
            print("❌ config.json 파일을 찾을 수 없습니다.")
            print(f"   경로: {config_file}")
            return 1

        print(f"✅ 설정 파일: {config_file}")

        # 필수 디렉토리 생성
        required_dirs = [
            project_root / "uploads",
            project_root / "processed_emails",
            project_root / "logs",
            project_root / "temp"
        ]

        for dir_path in required_dirs:
            dir_path.mkdir(exist_ok=True)
            print(f"📁 디렉토리 준비: {dir_path.name}")

        # Flask 앱 생성
        try:
            app = create_app(str(config_file))
            print("✅ Flask 애플리케이션 생성 완료")
        except Exception as e:
            print(f"❌ Flask 앱 생성 실패: {e}")
            return 1

        # 개발/운영 모드 설정
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', '5000'))

        print(f"\n🚀 서버 시작:")
        print(f"   주소: http://{host}:{port}")
        print(f"   디버그 모드: {'ON' if debug_mode else 'OFF'}")
        print(f"   환경: {'개발' if debug_mode else '운영'}")
        print("\n🔧 사용 가능한 기능:")
        print("   - mbox 파일 업로드 및 파싱")
        print("   - 이메일 목록 및 검색")
        print("   - 법정 증거 생성")
        print("   - 타임라인 시각화")
        print("   - 무결성 검증")
        print("\n📄 API 문서: http://{host}:{port}/api")
        print("=" * 60)

        try:
            app.run(debug=debug_mode, host=host, port=port, threaded=True)
        except KeyboardInterrupt:
            print("\n\n👋 서버가 정상적으로 종료되었습니다.")
        except Exception as e:
            print(f"\n❌ 서버 실행 오류: {e}")
            return 1

        return 0

    if __name__ == '__main__':
        sys.exit(main())

except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("필요한 패키지를 설치해주세요:")
    print("pip install -r requirements.txt")
    sys.exit(1)
