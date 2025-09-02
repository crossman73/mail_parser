#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 서버 시작 스크립트
법원 제출용 메일박스 증거 분류 시스템의 웹 인터페이스를 시작합니다.
"""

from src.web.app import create_app
import os
import sys

from flask import Flask

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 웹 애플리케이션 모듈 import


def main():
    """
    웹 서버를 시작합니다.
    """
    print("=" * 60)
    print("📧 법원 제출용 메일박스 증거 분류 시스템 - 웹 인터페이스")
    print("=" * 60)
    print("한국 법원의 디지털 증거 제출 규정을 준수하는")
    print("메일박스 증거 처리 및 분류 시스템의 웹 인터페이스입니다.")
    print("=" * 60)

    # Flask 애플리케이션 생성
    app = create_app()

    # 개발 모드 설정
    app.config['DEBUG'] = True

    print(f"🌐 웹 서버를 시작합니다...")
    print(f"📍 접속 주소: http://localhost:5000")
    print(f"💡 종료하려면 Ctrl+C를 누르세요")
    print("-" * 60)

    try:
        # 웹 서버 시작
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 개발 중 자동 재시작 비활성화
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  웹 서버가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 웹 서버 시작 중 오류 발생: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
